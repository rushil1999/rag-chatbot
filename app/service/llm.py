from app.service.llm_setup import x_api_client
from app.service.vector_search import get_closest_data_embedding_document
from app.models.vector_models import User_Chat_Payload
from fastapi import HTTPException
from app.models.response_models import Service_Response_Model
from app.service.logging import log_info,log_error


async def generate_llm_response(user_input, closest_vectors):
  log_info("User Data received {user_input}", user_input=user_input)
  try: 
    completion = x_api_client.chat.completions.create(
      model="grok-3-mini-fast",
      messages=[
        {
          "role": "system", 
          "content": f"You are Rushil's personal Assistant RAG Chatbot named Vini. Be concise, helpful. Don't give too long and elaborate answers. If the context does not contain the answer, provide a graceful response. Here are the closest vectors received from vector search in order of higher cosing similarity first: {closest_vectors}"},
        {"role": "user", "content": f"{user_input}"},
      ],
    )

    if len(completion.choices) > 0:
      log_info("Response generate from llm: {result}", result=completion.choices[0].message)
      return Service_Response_Model(data=completion.choices[0].message, is_success=True)
    return Service_Response_Model(data="", is_success=False, status_code=404, message="No data received from the API")
  except Exception as e:
    log_error("Error generating chat response with payload: {user_chat_payload}, due to {error}",user_chat_payload=user_chat_payload, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error getting response from Grok: {str(e)}")
