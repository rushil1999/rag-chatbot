from app.service.logging import log_info, log_error
from app.models.chat_models import Message_Payload, Message, Chat
from app.service.vector_db import vector_db
from app.models.response_models import Service_Response_Model
from app.models.vector_models import User_Chat_Payload
from app.service.llm import generate_llm_response
from fastapi import HTTPException
from bson import ObjectId
from app.service.vector_search import get_closest_data_embedding_document



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
      new_message = Message(message_text=message_payload.message_text, user_type=message_payload.user_type)
      chat = Chat(
        session_id=message_payload.session_id,
        messages=[
          new_message
        ]
      )
      data_dump =  chat.model_dump(by_alias=True)
      collection = vector_db['chat_data']
      result = collection.insert_one(data_dump).inserted_id
      return Service_Response_Model(data=str(result), is_success=True)
            
    doc_id = chat_response.data[0]['_id']
    log_info("Found existing document with session id {session_id} and document id {id}", session_id=message_payload.session_id, id=chat_response.data[0]['_id'])
    result = collection.update_one(
      {"_id": ObjectId(doc_id)},
      {"$push": {"messages": new_message.dict()}}
    )
    return await get_chat_by_session_id(message_payload.session_id)
  except Exception as e:
    log_error("Error Inserting chat data document payload: {message_payload}, due to {error}",message_payload=message_payload, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error inserting item: {str(e)}")


async def chat_response(message_payload: Message_Payload):
  log_info("Received Chat Response Payload {message_payload}", message_payload=message_payload)
  try:
    # Storing User message
    response = await store_chat_message(message_payload)
    if not response.is_success:
      return response
    
    session_id = message_payload.session_id
    user_input = message_payload.message_text

    bot_message_payload = Message_Payload(message_text="", session_id=session_id, user_type="bot")
    # Get Closest Vector
    response = await get_closest_data_embedding_document(user_input)
    if not response.is_success:
      if response.status_code == 404:
        bot_message_payload = Message_Payload(message_text="I think I don't have enough data to answer this question. Maybe Rushil didn't ingest enough vectors in the search Database. Can you please contact him for this.😅 ", session_id=session_id, user_type="bot")
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




async def get_chat_by_session_id(session_id: str):
  log_info("Received Session Id input {session_id}", session_id={session_id})
  try:
    result = []
    collection = vector_db['chat_data']
    cursor = collection.find({'session_id': session_id})
    for document in cursor:
      document['_id'] = str(document['_id'])
      result.append(document)
    if len(result) == 0:
      return Service_Response_Model(data=[], is_success=False, status_code=404,  message=f"No data found from for session id,{session_id}")
    return Service_Response_Model(data=result, is_success=True)
  except Exception as e:
    log_error("Error fetching chats by session id: {session_id}, due to {error}",session_id=session_id, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error inserting item: {str(e)}")



