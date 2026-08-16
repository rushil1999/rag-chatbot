import asyncio
import hashlib
from dotenv import load_dotenv
import os
from fastapi import HTTPException
from app.service.embedding import generate_vector_embeddings
from app.service.vector_db import vector_db, cosine_similarity_threshold
from app.models.vector_models import Data_Embedding, Data_Embedding_Payload
from app.service.logging import log_info, log_error
from app.models.response_models import Service_Response_Model




async def get_closest_data_embedding_document(message: str) -> str:
  log_info("User Input Message received: {message}", message=message)
  try:
    response = await generate_vector_embeddings(message)
    if not response.is_success:
      return response

    user_vector = response.data
    collection = vector_db['data_embeddings']
    pipeline = [
      {
          "$vectorSearch": {
              "queryVector": user_vector,
              "path": "text_embeddings",
              "numCandidates": 100,
              "limit": 5,
              "index": "vector_search"
          }
      },
      {
          '$project': {
            '_id': 1,
            'text': 1,
            'category': 1,
            'score': {
              '$meta': 'vectorSearchScore'
            }
          }
      },
      {
          "$sort": {
              "score": -1  # Descending order
          }
      }
    ]
    results = await asyncio.to_thread(lambda: list(collection.aggregate(pipeline)))

    if len(results) == 0:
      log_info("Vector search returned no candidates at all")
      return Service_Response_Model(data=[], status_code=404, is_success=False, message="No data found from vector search")

    # Strong matches clear the configured threshold; anything below is kept only
    # as best-effort, low-confidence context so the bot always has something to
    # work with instead of dead-ending on a 404.
    strong = []
    for i in results:
      item = {
        "text": i["text"],
        "category": i.get("category", "general"),
        "score": i["score"],
      }
      if i["score"] > cosine_similarity_threshold:
        strong.append(item)

    max_score = results[0]["score"]
    if strong:
      log_info("Found {count} strong matches (max score {max_score})", count=len(strong), max_score=max_score)
      return Service_Response_Model(data=strong, is_success=True)

    # Nothing cleared the threshold — fall back to the single best result as
    # low-confidence context. The LLM prompt (with the always-on profile) can
    # still produce a graceful, on-persona answer from it.
    best = results[0]
    log_info(
      "No strong matches (max score {max_score} < threshold {threshold}); returning best-effort context",
      max_score=max_score,
      threshold=cosine_similarity_threshold,
    )
    return Service_Response_Model(
      data=[{"text": best["text"], "category": best.get("category", "general"), "score": best["score"]}],
      is_success=True,
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error getting closest vector: {str(e)}")


async def insert_data_embeddings_document(data_embedding_payload: Data_Embedding_Payload):
  log_info("User Data received: {data_embedding_payload}", data_embedding_payload=data_embedding_payload)
  try:
    text = data_embedding_payload.text
    response = await generate_vector_embeddings(text, input_type="search_document")
    if not response.is_success:
      return response
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    data_embedding = Data_Embedding(
      text=text,
      category=data_embedding_payload.category,
      text_embeddings=response.data,
      source=data_embedding_payload.source,
      content_hash=content_hash,
    )

    data_dump = data_embedding.model_dump(by_alias=True)
    collection = vector_db['data_embeddings']
    # Upsert on content_hash so re-ingesting the same text updates in place
    # instead of creating duplicate vectors.
    result = await asyncio.to_thread(lambda: collection.update_one(
      {"content_hash": content_hash},
      {"$set": data_dump},
      upsert=True,
    ))
    inserted = result.upserted_id is not None
    log_info("Upserted data embedding (inserted={inserted}) for hash {hash}", inserted=inserted, hash=content_hash)
    return Service_Response_Model(data={"content_hash": content_hash, "inserted": inserted}, is_success=True)
  except Exception as e:
    log_error("Error Inserting data embedding document payload: {data_embedding_payload}, due to {error}",data_embedding_payload=data_embedding_payload, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error inserting item: {str(e)}")


async def delete_data_embeddings_by_source(source: str):
  """Delete every embedding previously ingested from a given source file.

  Used by the ingest script to prune stale chunks before re-inserting a file, so
  edits and deletions don't leave orphaned vectors behind.
  """
  log_info("Deleting existing embeddings for source: {source}", source=source)
  try:
    collection = vector_db['data_embeddings']
    result = await asyncio.to_thread(lambda: collection.delete_many({"source": source}))
    log_info("Deleted {count} existing embeddings for source {source}", count=result.deleted_count, source=source)
    return Service_Response_Model(data={"deleted": result.deleted_count}, is_success=True)
  except Exception as e:
    log_error("Error deleting embeddings for source {source}: {error}", source=source, error=str(e))
    raise HTTPException(status_code=500, detail=f"Error deleting embeddings: {str(e)}")


async def get_all_data_embedding_documents():
  log_info("Get All Data embeddings")
  try:
    collection = vector_db['data_embeddings']
    def _fetch_all():
      docs = []
      for document in collection.find({}):
        document['_id'] = str(document['_id'])
        docs.append(document)
      return docs
    return await asyncio.to_thread(_fetch_all)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error inserting item: {str(e)}")
