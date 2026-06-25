import asyncio
import json
from app.service.logging import log_info, log_error
from app.models.chat_models import Message_Payload, Message, Chat
from app.service.vector_db import vector_db
from app.models.response_models import Service_Response_Model
from app.models.vector_models import User_Chat_Payload
from app.service.llm import generate_llm_response, generate_llm_response_stream
from fastapi import HTTPException
from bson import ObjectId
from app.service.vector_search import get_closest_data_embedding_document


NO_CONTEXT_MESSAGE = "I think I don't have enough data to answer this question. Maybe Rushil didn't ingest enough vectors in the search Database. Can you please contact him for this.😅 "


async def store_chat_message(message_payload: Message_Payload):
  log_info("Received Chat Payload {message_payload}", message_payload=message_payload)
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
    log_error("Error Inserting chat data document payload: {message_payload}, due to {error}",message_payload=message_payload, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error inserting item: {str(e)}")


async def chat_response(message_payload: Message_Payload):
  log_info("Received Chat Response Payload {message_payload}", message_payload=message_payload)
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

    if not response.is_success:
      if response.status_code == 404:
        bot_message_payload = Message_Payload(message_text=NO_CONTEXT_MESSAGE, session_id=session_id, user_type="bot")
      else:
        return response
    else:
      # Generating response from LLM
      llm_response = await generate_llm_response(user_input, response.data)
      if not llm_response.is_success:
        return llm_response
      # Storing the LLM response
      bot_message_payload = Message_Payload(message_text=llm_response.data.content, session_id=session_id, user_type="bot")
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

    full_text = ""
    if not response.is_success:
      if response.status_code == 404:
        full_text = NO_CONTEXT_MESSAGE
        yield f"data: {json.dumps({'token': full_text})}\n\n"
      else:
        yield f"data: {json.dumps({'error': response.message})}\n\n"
        return
    else:
      async for delta in generate_llm_response_stream(user_input, response.data):
        full_text += delta
        yield f"data: {json.dumps({'token': delta})}\n\n"

    # Persist the complete bot message after streaming finishes
    bot_message_payload = Message_Payload(message_text=full_text, session_id=session_id, user_type="bot")
    await store_chat_message(bot_message_payload)
    log_info("Streamed response stored successfully in DB for session id: {session_id}", session_id=session_id)
    yield "data: [DONE]\n\n"
  except Exception as e:
    log_error("Error streaming chat response by session id: {session_id}, due to {error}", session_id=session_id, error=str(e))
    yield f"data: {json.dumps({'error': str(e)})}\n\n"


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
