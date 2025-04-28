from typing import Union
from fastapi import APIRouter
from app.service.embedding import generate_vector_embeddings
import httpx

router = APIRouter()


@router.get("/embeddings/{input}")
async def generate_embeddings(input: str):
  data = await generate_vector_embeddings(input)
  return {"result": data}


@router.get("/test")
def test():
    return {"success": "ok"}
