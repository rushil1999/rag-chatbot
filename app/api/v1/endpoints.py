from typing import Union
from fastapi import APIRouter,HTTPException
from app.service.embedding import generate_vector_embeddings
from app.service.vector_search import get_closest_vector
from app.service.vector_search import get_all_data_embedding_documents
from app.service.vector_search import insert_data_embeddings_document
from app.models.vector_models import Vector_Search_Payload
from app.models.vector_models import Data_Embedding_Payload
from app.models.vector_models import User_Chat_Payload
from app.service.llm import generate_chat_response
from app.models.response_models import Service_Response_Model

import httpx

router = APIRouter()


@router.get("/embeddings/{input}")
async def generate_embeddings_controller(input: str):
  data = await generate_vector_embeddings(input)
  return {"result": data}

@router.post("/vector/search/")
async def vector_search_controller(vector_search_payload: Vector_Search_Payload):
  message = vector_search_payload.message
  data = await get_closest_vector(vector_search_payload.message)
  return {"result": data}

@router.post("/data_embedding/")
async def insert_data_embeddings_document_controller(data_embedding_payload: Data_Embedding_Payload):
  data = await insert_data_embeddings_document(data_embedding_payload)
  return {"result": data}

@router.get("/data_embedding/all")
async def get_all_data_embedding_documents_controller():
  data = await get_all_data_embedding_documents()
  return {"result": data}

@router.post("/chat")
async def generate_chat_response_controller(user_chat_payload: User_Chat_Payload):
  response = await generate_chat_response(user_chat_payload)
  if not response.is_success:
    raise HTTPException(status_code=500, detail=response.message)
  return {"data": response.data}



@router.get("/test")
def test():
    return {"success": "ok"}
