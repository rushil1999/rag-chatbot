import asyncio
import json
from app.service.logging import log_info, log_error
from app.models.chat_models import Message_Payload, Message, Chat
from app.service.vector_db import vector_db
from app.models.response_models import Service_Response_Model
from app.service.llm import LLMStreamError, generate_llm_response, generate_llm_response_stream
from fastapi import HTTPException
from bson import ObjectId
from app.service.vector_search import get_closest_data_embedding_document


NO_CONTEXT_MESSAGE = (
  "I'm having trouble answering that one right now. Rushil is the best person to ask directly — "
  "you can reach him at shahrushil1999@gmail.com or on LinkedIn at "
  "https://linkedin.com/in/rushil1999."
)

# How many recent messages of a session to feed back into the LLM for continuity.
RECENT_TURNS = 10


def _recent_history(store_result):
  """Extract the last RECENT_TURNS messages from a stored-chat response."""
  try:
    messages = store_result.data[0].get("messages", [])
  except (IndexError, AttributeError, TypeError):
    return []
  return messages[-RECENT_TURNS:]


async def store_chat_message(message_payload: Message_Payload):
  # Log the shape, not the content — visitor messages shouldn't land in stdout logs.
  log_info(
    "Storing chat message for session {session_id} ({user_type}, {length} chars)",
    session_id=message_payload.session_id,
    user_type=message_payload.user_type,
    length=len(message_payload.message_text),
  )
  try:
    collection = vector_db['chat_data']
    new_message = Message(message_text=message_payload.message_text, user_type=message_payload.user_type)
    # Search if the session ID exists or not
    chat_response = await get_chat_by_session_id(message_payload.session_id)
    if not chat_response.is_success:
      if chat_response.status_code != 404:
        return chat_response
      log_info("No document found for {session_id}", session_id=message_payload.session_id)
      chat = Chat(
        session_id=message_payload.session_id,
        messages=[
          new_message
        ]
      )
      data_dump =  chat.model_dump(by_alias=True)
      result = await asyncio.to_thread(lambda: collection.insert_one(data_dump).inserted_id)
      return Service_Response_Model(data=str(result), is_success=True)

    doc_id = chat_response.data[0]['_id']
    log_info("Found existing document with session id {session_id} and document id {id}", session_id=message_payload.session_id, id=chat_response.data[0]['_id'])
    await asyncio.to_thread(lambda: collection.update_one(
      {"_id": ObjectId(doc_id)},
      {"$push": {"messages": new_message.dict()}}
    ))
    return await get_chat_by_session_id(message_payload.session_id)
  except Exception as e:
    log_error("Error storing chat message for session {session_id}: {error}", session_id=message_payload.session_id, error=str(e))
    raise HTTPException(status_code=500, detail=f"Error inserting item: {str(e)}")


async def chat_response(message_payload: Message_Payload):
  log_info("Chat turn for session {session_id}", session_id=message_payload.session_id)
  session_id = message_payload.session_id
  try:
    user_input = message_payload.message_text

    # Store the user message and retrieve context concurrently (independent work)
    store_result, response = await asyncio.gather(
      store_chat_message(message_payload),
      get_closest_data_embedding_document(user_input),
    )
    if not store_result.is_success:
      return store_result

    # A retrieval 404 just means no matching vectors — still answer from the
    # always-on profile + conversation history. Only a real error short-circuits.
    context = []
    if not response.is_success:
      if response.status_code != 404:
        return response
    else:
      context = response.data

    history = _recent_history(store_result)
    llm_response = await generate_llm_response(user_input, context, history)
    if not llm_response.is_success:
      bot_text = NO_CONTEXT_MESSAGE
    else:
      bot_text = llm_response.data.content
    bot_message_payload = Message_Payload(message_text=bot_text, session_id=session_id, user_type="bot")
    response = await store_chat_message(bot_message_payload)
    if not response.is_success:
      return response
    log_info("Response stored successfully in DB for session id: {session_id}", session_id=session_id)
    return await get_chat_by_session_id(session_id)
  except Exception as e:
    log_error("Error generating chat response by session id: {session_id}, due to {error}",session_id=session_id, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error generating chat response: {str(e)}")


async def chat_response_stream(message_payload: Message_Payload):
  """Async generator yielding SSE events as the bot answer is produced.

  Stores the user message, retrieves context, streams Grok tokens to the
  client, then persists the full bot message once the stream completes.
  """
  session_id = message_payload.session_id
  user_input = message_payload.message_text
  try:
    # Store the user message and retrieve context concurrently (independent work)
    store_result, response = await asyncio.gather(
      store_chat_message(message_payload),
      get_closest_data_embedding_document(user_input),
    )
    if not store_result.is_success:
      yield f"data: {json.dumps({'error': store_result.message})}\n\n"
      return

    # A retrieval 404 just means no matching vectors — still answer from the
    # always-on profile + conversation history. Only a real error short-circuits.
    context = []
    if not response.is_success:
      if response.status_code != 404:
        yield f"data: {json.dumps({'error': response.message})}\n\n"
        return
    else:
      context = response.data

    history = _recent_history(store_result)
    full_text = ""
    try:
      async for delta in generate_llm_response_stream(user_input, context, history):
        full_text += delta
        yield f"data: {json.dumps({'token': delta})}\n\n"
    except LLMStreamError as e:
      log_error("Grok stream failed for session id: {session_id}, due to {error}", session_id=session_id, error=str(e))
      # Nothing usable was produced — surface the friendly fallback rather than a raw error.
      if not full_text:
        full_text = NO_CONTEXT_MESSAGE
        yield f"data: {json.dumps({'token': full_text})}\n\n"

    # Persist the complete bot message after streaming finishes
    bot_message_payload = Message_Payload(message_text=full_text, session_id=session_id, user_type="bot")
    await store_chat_message(bot_message_payload)
    log_info("Streamed response stored successfully in DB for session id: {session_id}", session_id=session_id)
    yield "data: [DONE]\n\n"
  except Exception as e:
    log_error("Error streaming chat response by session id: {session_id}, due to {error}", session_id=session_id, error=str(e))
    yield f"data: {json.dumps({'error': 'Something went wrong generating that answer.'})}\n\n"
    yield "data: [DONE]\n\n"


async def get_chat_by_session_id(session_id: str):
  log_info("Received Session Id input {session_id}", session_id={session_id})
  try:
    collection = vector_db['chat_data']
    def _fetch():
      docs = []
      for document in collection.find({'session_id': session_id}):
        document['_id'] = str(document['_id'])
        docs.append(document)
      return docs
    result = await asyncio.to_thread(_fetch)
    if len(result) == 0:
      return Service_Response_Model(data=[], is_success=False, status_code=404,  message=f"No data found from for session id,{session_id}")
    return Service_Response_Model(data=result, is_success=True)
  except Exception as e:
    log_error("Error fetching chats by session id: {session_id}, due to {error}",session_id=session_id, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error inserting item: {str(e)}")
