from pydantic import BaseModel
from typing import List, Optional

class Vector_Search_Payload(BaseModel):
    message: str

class Data_Embedding_Payload(BaseModel):
    text: str
    category: str = "general"
    source: Optional[str] = None

class Data_Embedding(BaseModel):
    text: str
    category: str
    text_embeddings: List[float]
    source: Optional[str] = None
    content_hash: Optional[str] = None

class User_Chat_Payload(BaseModel):
    user_input: str
