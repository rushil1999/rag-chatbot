from app.service.llm_setup import x_api_client
from app.service.persona import PROFILE
from fastapi import HTTPException
from app.models.response_models import Service_Response_Model
from app.service.logging import log_info,log_error


# Map stored chat message user_type -> OpenAI/Grok chat role.
_ROLE_BY_USER_TYPE = {"user": "user", "bot": "assistant"}


def _format_context(closest_vectors):
  """Render retrieved vectors into a readable, category-tagged context block.

  Accepts either the new structured items ({text, category, score}) or a plain
  list of strings (backwards compatible).
  """
  if not closest_vectors:
    return ""
  lines = []
  for item in closest_vectors:
    if isinstance(item, dict):
      category = item.get("category", "general")
      lines.append(f"- [{category}] {item.get('text', '')}")
    else:
      lines.append(f"- {item}")
  return "\n".join(lines)


def _build_messages(user_input, closest_vectors, history=None):
  context_block = _format_context(closest_vectors)
  system_content = (
    "You are Vini, Rushil's personal assistant chatbot. You speak about Rushil in a warm, "
    "concise, helpful way. Prefer a few short points or short paragraphs; avoid long, elaborate answers.\n\n"
    "Authoritative background about Rushil (always trust this):\n"
    f"{PROFILE or '(no profile provided yet)'}\n\n"
    "Additional details retrieved from Rushil's knowledge base for this question, ordered by "
    "relevance (may be empty or only loosely relevant):\n"
    f"{context_block or '(no strong matches found)'}\n\n"
    "Use the background and retrieved details to answer. If the details don't cover the question, "
    "answer gracefully from the background you do have and, if truly unknown, say so briefly and "
    "suggest contacting Rushil — never fabricate specifics."
  )

  messages = [{"role": "system", "content": system_content}]

  # Recent conversation turns for continuity. The final stored message is the
  # current user_input (already appended below), so drop a trailing user turn
  # that duplicates it.
  turns = list(history or [])
  if turns and turns[-1].get("user_type") == "user" and turns[-1].get("message_text") == user_input:
    turns = turns[:-1]
  for turn in turns:
    role = _ROLE_BY_USER_TYPE.get(turn.get("user_type"))
    text = turn.get("message_text")
    if role and text:
      messages.append({"role": role, "content": text})

  messages.append({"role": "user", "content": f"{user_input}"})
  return messages


async def generate_llm_response(user_input, closest_vectors, history=None):
  log_info("User Data received {user_input}", user_input=user_input)
  try:
    completion = await x_api_client.chat.completions.create(
      model="grok-3-mini-fast",
      messages=_build_messages(user_input, closest_vectors, history),
    )

    if len(completion.choices) > 0:
      log_info("Response generate from llm: {result}", result=completion.choices[0].message)
      return Service_Response_Model(data=completion.choices[0].message, is_success=True)
    return Service_Response_Model(data="", is_success=False, status_code=404, message="No data received from the API")
  except Exception as e:
    log_error("Error generating chat response with input: {user_input}, due to {error}",user_input=user_input, error=str(e) )
    raise HTTPException(status_code=500, detail=f"Error getting response from Grok: {str(e)}")


async def generate_llm_response_stream(user_input, closest_vectors, history=None):
  """Yields response text deltas from Grok as they are generated."""
  log_info("User Data received (stream) {user_input}", user_input=user_input)
  try:
    stream = await x_api_client.chat.completions.create(
      model="grok-3-mini-fast",
      messages=_build_messages(user_input, closest_vectors, history),
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
