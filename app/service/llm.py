from app.service.llm_setup import x_api_client
from app.service.vector_search import get_closest_data_embedding_document
from app.models.vector_models import User_Chat_Payload
from fastapi import HTTPException
from app.models.response_models import Service_Response_Model
from app.service.logging import log_info,log_error


def _build_messages(user_input, closest_vectors):
  return [
    {
      "role": "system",
      "content": f"You are Rushil's personal Assistant RAG Chatbot named Vini. Be concise, helpful, and give the answer in multiple points or paragraphs if needed. Don't give too long and elaborate answers. If the context does not contain the answer, provide a graceful response. Here are the closest vectors received from vector search in order of higher cosing similarity first: {closest_vectors}"},
    {"role": "user", "content": f"{user_input}"},
  ]


async def generate_llm_response(user_input, closest_vectors):
  log_info("User Data received {user_input}", user_input=user_input)
  try:
    completion = await x_api_client.chat.completions.create(
      model="grok-3-mini-fast",
      messages=_build_messages(user_input, closest_vectors),
    )

    if len(completion.choices) > 0:
      log_info("Response generate from llm: {result}", result=completion.choices[0].message)
      return Service_Response_Model(data=completion.choices[0].message, is_success=True)
    return Service_Response_Model(data="", is_success=False, status_code=404, message="No data received from the API")
  except Exception as e:
    log_error("Error generating chat response with input: {user_input}, due to {error}",user_input=user_input, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error getting response from Grok: {str(e)}")


async def generate_llm_response_stream(user_input, closest_vectors):
  """Yields response text deltas from Grok as they are generated."""
  log_info("User Data received (stream) {user_input}", user_input=user_input)
  try:
    stream = await x_api_client.chat.completions.create(
      model="grok-3-mini-fast",
      messages=_build_messages(user_input, closest_vectors),
      stream=True,
    )
    async for chunk in stream:
      if not chunk.choices:
        continue
      delta = chunk.choices[0].delta.content
      if delta:
        yield delta
  except Exception as e:
    log_error("Error streaming chat response with input: {user_input}, due to {error}",user_input=user_input, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error getting response from Grok: {str(e)}")
