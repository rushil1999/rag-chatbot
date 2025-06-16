from pydantic import BaseModel
from typing import List

class Message_Payload(BaseModel):
    message_text: str
    session_id: str
    user_type: str
  

class Message(BaseModel):
  message_text: str
  user_type: str

class Chat(BaseModel):
    session_id: str
    messages: List[Message]
