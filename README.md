# rag-chatbot

Vini — a Retrieval-Augmented Generation personal chatbot that answers recruiter questions about
Rushil. Powers the chat widget on the [portfolio](https://rushil1999.github.io/portfolio).

[Medium write-up](https://medium.com/@rushil1999.dev/vini-a-retrieval-augmented-generation-personal-chatbot-7b90635b595e)

## Run

```bash
uvicorn app.main:app --reload
```

Copy `.env.example` to `app/.env` and fill it in. Env vars are loaded from `app/.env` via
`app/env.py` regardless of the working directory, and real environment variables always win (so
container deploys can inject config directly).

Retrieval needs an Atlas Vector Search index named `vector_search` on the `data_embeddings`
collection, indexing the `text_embeddings` field.

## Vini's knowledge

### Core bio (always-on)

`app/data/profile.md` is injected into **every** answer, so Vini stays on-persona even when
vector search finds little. Keep it short — it costs tokens on every request.

### The corpus

`content/` holds the version-controlled knowledge base — bio, one file per role, education,
skills, projects, and a recruiter FAQ. It is the single source of truth: re-ingesting replaces
what is in MongoDB, so edit the markdown, never the database.

```bash
python -m scripts.ingest ./content
```

Chunking is heading-aware: each `##` section becomes its own chunk, prefixed with the document's
`#` title so a chunk about "Autosweep" still says "Tesla". Ingestion is idempotent and atomic per
file — every chunk is embedded first, and the file's old chunks are only pruned once the full
replacement is in hand, so a rate limit can't leave a half-populated knowledge base.

Re-running is safe. Files you delete from disk aren't pruned automatically — remove them, or
re-ingest the whole folder, to drop their chunks. Single facts can also be added via
`POST /vector/` with `{ "text": "...", "category": "..." }` (admin token required).

Guardrails live in the system prompt (`app/service/llm.py`): Vini never discusses compensation,
notice period, work authorization, or reasons for leaving a role, never shares Rushil's phone
number, and redirects off-topic or persona-override attempts.

## API

| Endpoint | Token | Purpose |
|---|---|---|
| `POST /chat/stream` | public | Streaming (SSE) response — what the site uses |
| `POST /chat/response` | public | Non-streaming response |
| `GET /test` | public | Health check; the site pings it to wake the service |
| `POST /vector/`, `GET /vector/all`, `POST /vector/search/`, `GET /vector/embeddings/{input}` | admin | Knowledge-base management |
| `POST /chat/`, `GET /chat/{session_id}` | admin | Transcript access |

Chat endpoints accept `{ "message_text": "...", "session_id": "...", "user_type": "user" }` and
keep per-session memory, so follow-up questions stay in context.

`/chat/stream` emits `data: {"token": "..."}` frames, terminated by `data: [DONE]`; errors arrive
as `data: {"error": "..."}`.

### Auth

Two tokens. `PUBLIC_TOKEN` ships inside the portfolio bundle — it is **not a secret**, so it only
reaches the chat endpoints and is rate limited per client (20 requests / 10 min by default).
`ADMIN_TOKEN` guards everything that writes to the knowledge base or reads transcripts, and must
never appear in frontend code. `USER_TOKEN` is still accepted as the public token for backwards
compatibility; drop it once the frontend ships a `PUBLIC_TOKEN`.

CORS is an allowlist (`ALLOWED_ORIGINS`), defaulting to the portfolio origin and localhost.
