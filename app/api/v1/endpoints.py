from typing import Union
from fastapi import APIRouter,HTTPException
from app.service.embedding import generate_vector_embeddings
from app.service.vector_search import get_closest_data_embedding_document, get_all_data_embedding_documents, insert_data_embeddings_document
from app.models.vector_models import Vector_Search_Payload, Data_Embedding_Payload, User_Chat_Payload
from app.service.llm import generate_llm_response
from app.models.response_models import Service_Response_Model
from app.models.chat_models import Message_Payload
from app.service.chat import store_chat_message, chat_response, get_chat_by_session_id
import httpx

router = APIRouter()


@router.get("/vector/embeddings/{input}")
async def generate_embeddings_controller(input: str):
  data = await generate_vector_embeddings(input)
  return {"result": data}

@router.post("/vector/search/")
async def vector_search_controller(vector_search_payload: Vector_Search_Payload):
  message = vector_search_payload.message
  data = await get_closest_data_embedding_document(vector_search_payload.message)
  return {"result": data}

@router.post("/vector/")
async def insert_data_embeddings_document_controller(data_embedding_payload: Data_Embedding_Payload):
  data = await insert_data_embeddings_document(data_embedding_payload)
  return {"result": data}

@router.get("/vector/all")
async def get_all_data_embedding_documents_controller():
  data = await get_all_data_embedding_documents()
  return {"result": data}

@router.post("/llm")
async def generate_llm_response_controller(user_chat_payload: User_Chat_Payload):
  response = await generate_llm_response(user_chat_payload)
  if not response.is_success:
    if response.status_code == None:
      response.status_code = 500
    raise HTTPException(status_code=response.status_code, detail=response.message)
  return {"result": response.data}


@router.post("/chat/response")
async def chat_response_controller(message_payload: Message_Payload):
  response = await chat_response(message_payload)
  if not response.is_success:
    if response.status_code == None:
      response.status_code = 500
    raise HTTPException(status_code=response.status_code, detail=response.message)
  return {"result": response.data}


@router.post("/chat/")
async def store_chat_message_controller(message_payload: Message_Payload):
  data = await store_chat_message(message_payload)
  return {"result": data}

@router.get("/chat/{session_id}")
async def get_chat_by_session_id_controller(session_id: str):
  response = await get_chat_by_session_id(session_id)
  if not response.is_success:
    if response.status_code == None:
      response.status_code = 500
    raise HTTPException(status_code=response.status_code, detail=response.message)
  return {"result": response.data}

@router.get("/test")
def test():
    return {"success": "ok"}
