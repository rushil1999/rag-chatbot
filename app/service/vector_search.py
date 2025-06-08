from dotenv import load_dotenv
import os
from fastapi import HTTPException
from app.service.embedding import generate_vector_embeddings
from app.service.vector_db import vector_collection
from app.models.vector_models import Data_Embedding
from app.models.vector_models import Data_Embedding_Payload
import numpy as np


async def get_closest_vector(message: str) -> str:
  print(f"Service Log: User Input Message received {message}")
  user_vector = await generate_vector_embeddings(message)
  results = vector_collection.aggregate([
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
    }
  ])


  max_score = 0
  resposne = ""
  for i in results:
    score = i['score']
    if score > max_score:
      max_score = score
      response = i['text']
    
  print(f"Service Log: Text with highest cosine similarity: {max_score} is {resposne}")
  return response


async def insert_data_embeddings_document(data_embedding_payload: Data_Embedding_Payload):
  print(f"Service Log: User Data received {data_embedding_payload}")
  try: 
    text = data_embedding_payload.text
    print("Generating for text", text)
    generated_vectors = await generate_vector_embeddings(text)


    data_embedding = Data_Embedding(
      text=text,
      category=data_embedding_payload.category,
      text_embeddings=generated_vectors
    )

    data_dump =  data_embedding.model_dump(by_alias=True)
    result = vector_collection.insert_one(data_dump).inserted_id
    return str(result)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error inserting item: {str(e)}")
