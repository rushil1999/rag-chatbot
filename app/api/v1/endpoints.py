from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.chat_models import Message_Payload
from app.models.response_models import Service_Response_Model
from app.models.vector_models import Data_Embedding_Payload, Vector_Search_Payload
from app.service.chat import chat_response, chat_response_stream, get_chat_by_session_id, store_chat_message
from app.service.embedding import generate_vector_embeddings
from app.service.vector_search import (
  get_all_data_embedding_documents,
  get_closest_data_embedding_document,
  insert_data_embeddings_document,
)

router = APIRouter()


def _unwrap(response: Service_Response_Model):
  """Return a successful response's data, or raise the failure as an HTTP error."""
  if not response.is_success:
    raise HTTPException(status_code=response.status_code or 500, detail=response.message)
  return response.data


@router.get("/vector/embeddings/{input}")
async def generate_embeddings_controller(input: str):
  data = await generate_vector_embeddings(input)
  return {"result": data}


@router.post("/vector/search/")
async def vector_search_controller(vector_search_payload: Vector_Search_Payload):
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


@router.post("/chat/response")
async def chat_response_controller(message_payload: Message_Payload):
  return {"result": _unwrap(await chat_response(message_payload))}


@router.post("/chat/stream")
async def chat_response_stream_controller(message_payload: Message_Payload):
  return StreamingResponse(
    chat_response_stream(message_payload),
    media_type="text/event-stream",
    headers={
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  )


@router.post("/chat/")
async def store_chat_message_controller(message_payload: Message_Payload):
  data = await store_chat_message(message_payload)
  return {"result": data}


@router.get("/chat/{session_id}")
async def get_chat_by_session_id_controller(session_id: str):
  return {"result": _unwrap(await get_chat_by_session_id(session_id))}


@router.get("/test")
def test():
  return {"success": "ok"}
