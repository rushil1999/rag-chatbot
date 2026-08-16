"""Bulk-ingest a folder of notes into Vini's vector store.

Usage:
    python -m scripts.ingest <folder> [--category NAME]

Walks <folder> for .md / .txt (and .pdf if `pypdf` is installed), splits each
file into overlapping chunks, embeds every chunk, and upserts it into MongoDB.
Re-running is safe: chunks are keyed by content hash, so unchanged text updates
in place instead of creating duplicates.

Requires MONGODB_URI and COHERE_EMBEDDING_API_KEY to be available (loaded from
app/.env if present, otherwise from the environment).
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load env before importing app modules — app.service.vector_db connects to
# MongoDB at import time using MONGODB_URI.
_ENV = Path(__file__).resolve().parent.parent / "app" / ".env"
load_dotenv(_ENV)

from app.models.vector_models import Data_Embedding_Payload  # noqa: E402
from app.service.embedding import generate_vector_embeddings  # noqa: E402
from app.service.vector_search import (  # noqa: E402
  delete_data_embeddings_by_source,
  insert_data_embeddings_document,
)

SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}

# Chunks shorter than this are headings or stubs, not answers worth retrieving.
MIN_CHUNK_WORDS = 12


def _split_paragraphs(text: str, target_words: int, overlap_words: int):
  """Split text into paragraph-aware chunks of ~target_words with light overlap."""
  paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
  chunks = []
  current: list[str] = []  # accumulated words for the current chunk

  for paragraph in paragraphs:
    words = paragraph.split()
    if current and len(current) + len(words) > target_words:
      chunks.append(" ".join(current))
      current = current[-overlap_words:] if overlap_words else []
    current.extend(words)

  if current:
    chunks.append(" ".join(current))
  return chunks


def chunk_text(text: str, target_words: int = 220, overlap_words: int = 40):
  """Split markdown into retrievable chunks, one per `##` section where possible.

  Sections are the natural retrieval unit here — a section answers one question ("what was
  Autosweep?"). Splitting purely on word count would instead merge unrelated sections into one
  embedding, blurring what each vector means.

  Every chunk is prefixed with the document's `#` title, because chunks are retrieved without
  their filename: a chunk about "Autosweep" is useless if it doesn't also say "Tesla".
  """
  lines = text.split("\n")

  title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), "")

  # Group lines into sections, breaking at every `##` heading.
  sections: list[list[str]] = [[]]
  for line in lines:
    if line.startswith("## "):
      sections.append([])
    sections[-1].append(line)

  chunks = []
  for section in sections:
    body = "\n".join(section).strip()
    if not body:
      continue
    for piece in _split_paragraphs(body, target_words, overlap_words):
      # A section that is only its own heading (e.g. a document whose H1 is followed straight
      # away by an H2) carries no information — embedding it just adds noise to the search.
      if len(piece.split()) < MIN_CHUNK_WORDS:
        continue
      # Don't repeat the title when the chunk already opens with it (the preamble section,
      # whose first line is the `#` heading itself).
      already_titled = title and piece.lstrip("# ").startswith(title)
      chunks.append(piece if not title or already_titled else f"{title} — {piece}")
  return chunks


def read_file(path: Path):
  """Return the text content of a supported file, or None if unreadable."""
  suffix = path.suffix.lower()
  if suffix in (".md", ".txt"):
    return path.read_text(encoding="utf-8", errors="ignore")
  if suffix == ".pdf":
    try:
      from pypdf import PdfReader
    except ImportError:
      print(f"  skip {path.name}: install pypdf for PDF support (`pip install pypdf`)")
      return None
    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)
  return None


# Cohere's embed endpoint rate limits bulk ingests, and a rejected chunk means a silent hole in
# the knowledge base. Pace the calls and retry with backoff rather than dropping the chunk.
EMBED_DELAY_SECONDS = 0.5
EMBED_MAX_ATTEMPTS = 5


async def _embed_with_retry(text: str):
  """Embed one chunk, retrying with exponential backoff. Returns the vector, or None."""
  for attempt in range(EMBED_MAX_ATTEMPTS):
    if attempt:
      backoff = EMBED_DELAY_SECONDS * (2 ** attempt)
      print(f"  rate limited, retrying in {backoff:.1f}s (attempt {attempt + 1}/{EMBED_MAX_ATTEMPTS})")
      await asyncio.sleep(backoff)
    try:
      response = await generate_vector_embeddings(text, input_type="search_document")
    except Exception as e:
      # Transport failures surface as raised HTTPExceptions rather than a failed result, and
      # they are just as retryable as a 429.
      print(f"  embed call failed: {e}")
      continue
    if response.is_success:
      await asyncio.sleep(EMBED_DELAY_SECONDS)
      return response.data
  return None


async def ingest_folder(folder: str, category_override: str | None):
  root = Path(folder)
  files = sorted(p for p in root.rglob("*") if p.suffix.lower() in SUPPORTED_SUFFIXES)
  if not files:
    print(f"No .md/.txt/.pdf files found in {root}")
    return

  total_new = total_updated = total_skipped = total_pruned = 0
  for f in files:
    text = read_file(f)
    if not text or not text.strip():
      print(f"{f.name}: empty or unreadable, skipped")
      continue

    category = category_override or f.stem
    source = str(f.relative_to(root))
    chunks = chunk_text(text)

    # Embed everything before touching the database. Pruning first and then failing partway
    # through (a rate limit, a dropped connection) would leave the file half-represented in the
    # knowledge base, so a file is only replaced once its full replacement is in hand.
    embeddings = []
    for chunk in chunks:
      vector = await _embed_with_retry(chunk)
      if vector is None:
        break
      embeddings.append(vector)

    if len(embeddings) != len(chunks):
      total_skipped += len(chunks)
      print(f"{f.name}: embedding failed after retries — left unchanged ({len(chunks)} chunks skipped)")
      continue

    # Prune chunks previously ingested from this file so edits and removals don't
    # leave stale vectors behind, then insert the current chunks fresh.
    prune = await delete_data_embeddings_by_source(source)
    pruned = prune.data.get("deleted", 0) if prune.is_success else 0
    total_pruned += pruned

    new = updated = 0
    for chunk, vector in zip(chunks, embeddings):
      payload = Data_Embedding_Payload(text=chunk, category=category, source=source)
      result = await insert_data_embeddings_document(payload, embedding=vector)
      if not result.is_success:
        total_skipped += 1
        continue
      if result.data.get("inserted"):
        new += 1
      else:
        updated += 1
    total_new += new
    total_updated += updated
    print(f"{f.name}: pruned {pruned}, {len(chunks)} chunks -> {new} new, {updated} updated  [{category}]")

  print(f"\nDone. {total_new} new, {total_updated} updated, {total_pruned} pruned, {total_skipped} skipped.")


def main():
  parser = argparse.ArgumentParser(
    description="Ingest a folder of notes (.md/.txt/.pdf) into Vini's vector store.",
  )
  parser.add_argument("folder", help="Folder to ingest (searched recursively)")
  parser.add_argument(
    "--category",
    help="Category to tag every chunk with (default: each file's name)",
  )
  args = parser.parse_args()

  if not os.path.isdir(args.folder):
    print(f"Not a folder: {args.folder}")
    sys.exit(1)

  asyncio.run(ingest_folder(args.folder, args.category))


if __name__ == "__main__":
  main()
