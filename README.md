# rag-chatbot

Vini — a Retrieval-Augmented Generation personal chatbot that answers questions about Rushil.

[Medium write-up](https://medium.com/@rushil1999.dev/vini-a-retrieval-augmented-generation-personal-chatbot-7b90635b595e)

## Run

```bash
uvicorn app.main:app --reload
```

Requires `MONGODB_URI`, `COHERE_EMBEDDING_API_KEY`, `GROK_API_KEY`, and `USER_TOKEN`
(loaded from `app/.env` or the environment).

## Give Vini context about you

### Core bio (always-on)

`app/data/profile.md` is an editable markdown bio that is injected into **every** answer,
so Vini stays on-persona even when vector search finds little. Edit it to describe who you are.

### Bulk-ingest notes

Drop a folder of `.md` / `.txt` (or `.pdf`) notes anywhere and load them all in one command:

```bash
python -m scripts.ingest ./my-notes                 # category = each file's name
python -m scripts.ingest ./my-notes --category bio  # override the category
```

The script chunks each file, embeds every chunk, and upserts it into MongoDB. Re-running is
safe: before re-inserting a file, its previously-ingested chunks (matched by source path) are
pruned, so edits and deletions never leave stale vectors behind. PDF support needs `pypdf`
(already in `requirements.txt`).

Note: the source path is relative to the folder you pass, so re-run from the same folder for
pruning to match. Files you delete from disk aren't pruned automatically — remove them, or
re-ingest the whole folder, to drop their chunks.

Single facts can still be added via `POST /vector/` with `{ "text": "...", "category": "..." }`.

## Chat

- `POST /chat/stream` — streaming (SSE) response; recommended.
- `POST /chat/response` — non-streaming response.

Both accept `{ "message_text": "...", "session_id": "...", "user_type": "user" }` and keep
per-session memory, so follow-up questions stay in context.
