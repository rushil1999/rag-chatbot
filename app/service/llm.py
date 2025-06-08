from app.service.llm_setup import x_api_client
from app.service.vector_search import get_closest_vector
from app.models.vector_models import User_Chat_Payload

async def generate_chat_response(user_chat_payload: User_Chat_Payload):
  print(f"Service Log: User Data received {user_chat_payload}")
  try: 
    user_input = user_chat_payload.user_input
    get_closest_vector_text = await get_closest_vector(user_input)

    completion = x_api_client.chat.completions.create(
      model="grok-3-mini-fast",
      messages=[
        {
          "role": "system", 
          "content": f"You are a personal Chatbot. Here is the closest vector received from vector search: {get_closest_vector_text}"},
        {"role": "user", "content": f"{user_input}"},
      ],
    )

    print(completion.choices[0].message)
    return completion.choices[0].message
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error getting response from Grok: {str(e)}")
