from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from pydantic_core import core_schema
from pydantic import GetJsonSchemaHandler

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler):
        return {'type': 'string'}

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_after_validator_function(
                cls.validate,
                core_schema.str_schema()
            )
        )

    @classmethod
    def validate(cls, value: str) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError(f"Invalid ObjectId: {value}")
        return ObjectId(value)

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