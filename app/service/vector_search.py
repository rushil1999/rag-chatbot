from dotenv import load_dotenv
import os
from app.service.embedding import generate_vector_embeddings
from app.service.vector_db import vector_collection
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

