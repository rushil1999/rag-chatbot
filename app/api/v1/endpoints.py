from typing import Union
from fastapi import APIRouter
from app.service.embedding import generate_vector_embeddings
from app.service.vector_search import get_closest_vector
from app.models.vector_models import Vector_Search_Payload
import httpx

router = APIRouter()


@router.get("/embeddings/{input}")
async def generate_embeddings(input: str):
  data = await generate_vector_embeddings(input)
  return {"result": data}

@router.post("/vector/search/")
async def vector_search(vector_search_payload: Vector_Search_Payload):
  message = vector_search_payload.message
  data = await get_closest_vector(vector_search_payload.message)
  return {"result": data}

@router.get("/store/all")
async def get_all_vectors_controller():
  data = await get_all_vectors()
  return {"result": data}

@router.get("/test")
def test():
    return {"success": "ok"}
