import app.env  # noqa: F401  (loads .env before anything reads os.getenv)
import os
import secrets
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from app.service.logging import log_info



# Routes the public site is allowed to reach with the browser-visible token. Everything else
# (vector writes, embedding generation, reading arbitrary transcripts) needs the admin token,
# which never ships to the client.
PUBLIC_PATHS = frozenset({"/chat/response", "/chat/stream", "/test"})

# Chat endpoints cost money per call, so they are rate limited per client.
RATE_LIMITED_PATHS = frozenset({"/chat/response", "/chat/stream"})
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "600"))

# client key -> timestamps of recent requests. In-process only: a single instance is all this
# deployment runs, and the goal is blunting casual abuse, not distributed quota enforcement.
_request_log: dict[str, deque] = defaultdict(deque)


def _tokens():
  """Return (public_token, admin_token).

  USER_TOKEN is still honoured as the public token so the currently deployed site keeps working
  through a rollout; set PUBLIC_TOKEN and drop USER_TOKEN once the frontend is redeployed.
  """
  # Both are accepted at once so the public token can be rotated without downtime: deploy the
  # new PUBLIC_TOKEN while the old USER_TOKEN still works, redeploy the site, then drop
  # USER_TOKEN. Returning either/or would break the live site the moment PUBLIC_TOKEN is set.
  public = [t for t in (os.getenv("PUBLIC_TOKEN"), os.getenv("USER_TOKEN")) if t]
  admin = os.getenv("ADMIN_TOKEN")
  return public, admin


def _token_matches(presented: str | None, expected) -> bool:
  """Constant-time compare against one expected token or a list of accepted ones."""
  if not presented or not expected:
    return False
  candidates = [expected] if isinstance(expected, str) else expected
  # Compare against every candidate rather than short-circuiting, so timing doesn't reveal
  # which token matched.
  return any(secrets.compare_digest(presented, f"Bearer {c}") for c in candidates if c)


def _client_key(request: Request) -> str:
  # Prefer the proxy-forwarded client IP; Northflank terminates TLS in front of the app.
  forwarded = request.headers.get("x-forwarded-for")
  if forwarded:
    return forwarded.split(",")[0].strip()
  return request.client.host if request.client else "unknown"


def _is_rate_limited(key: str) -> bool:
  now = time.monotonic()
  window_start = now - RATE_LIMIT_WINDOW_SECONDS
  hits = _request_log[key]
  while hits and hits[0] < window_start:
    hits.popleft()
  if len(hits) >= RATE_LIMIT_MAX_REQUESTS:
    return True
  hits.append(now)
  return False


async def log_request(request: Request, call_next):
  start_time = time.perf_counter()
  response = await call_next(request)
  process_time = time.perf_counter() - start_time
  log_info(
    "{method} {path} -> {status} in {duration:.3f}s",
    method=request.method,
    path=request.url.path,
    status=response.status_code,
    duration=process_time,
  )
  response.headers["X-Process-Time"] = str(process_time)
  return response


async def authenticate_request(request: Request, call_next):
  if request.method == "OPTIONS":
    return await call_next(request)

  path = request.url.path
  presented = request.headers.get("authorization")
  public_token, admin_token = _tokens()

  # The admin token opens everything; the public token only opens the chat surface.
  is_admin = _token_matches(presented, admin_token)
  authorized = is_admin or (path in PUBLIC_PATHS and _token_matches(presented, public_token))

  if not authorized:
    log_info("Unauthorized {method} {path}", method=request.method, path=path)
    return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

  if not is_admin and path in RATE_LIMITED_PATHS and _is_rate_limited(_client_key(request)):
    log_info("Rate limited {method} {path}", method=request.method, path=path)
    return JSONResponse(
      status_code=429,
      content={"detail": "Too many messages. Please wait a moment before asking again."},
    )

  return await call_next(request)
