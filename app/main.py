import app.env as _env  # noqa: F401  (loads .env before anything reads os.getenv)
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import router as endpoints_router
from app.middlewares.http_request import authenticate_request, log_request


# Debug mode leaks tracebacks to clients, so it stays off unless explicitly enabled.
app = FastAPI(debug=os.getenv("DEBUG", "").lower() in ("1", "true", "yes"))

# Only the portfolio (and local dev) may call this API from a browser. No credentials are used —
# auth travels in the Authorization header — so allow_credentials stays off.
DEFAULT_ORIGINS = "https://rushil1999.github.io,http://localhost:3000"
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Middleware runs bottom-up, so logging wraps auth and records rejected requests too.
app.middleware("http")(authenticate_request)
app.middleware("http")(log_request)

app.include_router(endpoints_router)


# To start the app, go to root folder, outside of /app
# Run uvicorn app.main:app --reload
