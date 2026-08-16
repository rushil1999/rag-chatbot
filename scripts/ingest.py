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
from app.service.vector_search import (  # noqa: E402
  delete_data_embeddings_by_source,
  insert_data_embeddings_document,
)

SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}


def chunk_text(text: str, target_words: int = 500, overlap_words: int = 50):
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

    # Prune chunks previously ingested from this file so edits and removals don't
    # leave stale vectors behind, then insert the current chunks fresh.
    prune = await delete_data_embeddings_by_source(source)
    pruned = prune.data.get("deleted", 0) if prune.is_success else 0
    total_pruned += pruned

    chunks = chunk_text(text)
    new = updated = 0
    for chunk in chunks:
      payload = Data_Embedding_Payload(text=chunk, category=category, source=source)
      result = await insert_data_embeddings_document(payload)
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
