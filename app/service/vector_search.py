from dotenv import load_dotenv
import os
from fastapi import HTTPException
from app.service.embedding import generate_vector_embeddings
from app.service.vector_db import vector_db, cosine_similarity_threshold
from app.models.vector_models import Data_Embedding, Data_Embedding_Payload
from app.service.logging import log_info, log_error
from app.models.response_models import Service_Response_Model
import numpy as np




async def get_closest_data_embedding_document(message: str) -> str:
  log_info("User Input Message received: {message}", message=message)
  try:
    response = await generate_vector_embeddings(message)
    if not response.is_success:
      return response
    
    user_vector = response.data
    collection = vector_db['data_embeddings']
    results = collection.aggregate([
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
    ])


    max_score = 0
    response = []
    for i in results:
      score = i['score']
      if score > max_score:
        max_score = score
      if score > cosine_similarity_threshold:
        response.append(i['text'])
      
    log_info("Texts with high cosine similarities are {response}. With highest similarity {max_score}", response=response, max_score=max_score)
    if len(response) > 0:
      return Service_Response_Model(data=response, is_success=True)
    else: 
      log_info("No text with high cosine similarities found, max score is: {ma_score} and threshold is {threshold}", max_score=max_score, threshold=cosine_similarity_threshold )
      return Service_Response_Model(data=[], status_code=404, is_success=False, message=f"No data found from vector search, max_score: {max_score}")
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error getting closest vector: {str(e)}")


async def insert_data_embeddings_document(data_embedding_payload: Data_Embedding_Payload):
  log_info("User Data received: {data_embedding_payload}", data_embedding_payload=data_embedding_payload)
  try: 
    text = data_embedding_payload.text
    response = await generate_vector_embeddings(text)
    if not response.is_success:
      return response
    data_embedding = Data_Embedding(
      text=text,
      category=data_embedding_payload.category,
      text_embeddings=response.data
    )

    data_dump =  data_embedding.model_dump(by_alias=True)
    collection = vector_db['data_embeddings']
    result = collection.insert_one(data_dump).inserted_id
    return Service_Response_Model(data=str(result), is_success=False)
  except Exception as e:
    log_error("Error Inserting data embedding document payload: {data_embedding_payload}, due to {error}",data_embedding_payload=data_embedding_payload, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error inserting item: {str(e)}")


async def get_all_data_embedding_documents():
  log_info("Get All Data embeddings")
  try: 
    result = []
    collection = vector_db['data_embeddings']
    cursor = collection.find({})
    for document in cursor:
      document['_id'] = str(document['_id'])
      result.append(document)
    return result
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error inserting item: {str(e)}")

