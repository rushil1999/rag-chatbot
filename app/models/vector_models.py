from pydantic import BaseModel
from typing import List

class Vector_Search_Payload(BaseModel):
    message: str

class Data_Embedding_Payload(BaseModel):
    text: str
    category: str

class Data_Embedding(BaseModel):
    text: str
    category: str
    text_embeddings: List[float]

class User_Chat_Payload(BaseModel):
    user_input: str