import httpx

from dotenv import load_dotenv
from fastapi import HTTPException
import os
from app.service.logging import log_info, log_error
from app.models.response_models import Service_Response_Model

# Load environment variables from .env
load_dotenv()

# Function to get the API key from the environment
def get_api_key():
    return os.getenv("COHERE_EMBEDDING_API_KEY")

async def generate_vector_embeddings(input: str):
    log_info("Received Input: {input}", input=input)
    try:
        key = get_api_key()
        url = "https://api.cohere.com/v2/embed"

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        data = {
            "model": "embed-v4.0",
            "texts": [input],
            "input_type": "classification",
            "embedding_types": ["float"]
        }
        response = httpx.post(url, json=data, headers=headers)
        log_info("Called Cohere API to generate vectos, data: {data}", data=data)
        if response.status_code != httpx.codes.OK :
            log_error("Error fetching data from Cohere API, status code: {status_code}", status_code=response.status_code )
        embeddings_data = response.json()
        if embeddings_data["embeddings"] == None or embeddings_data["embeddings"]["float"] == None or len(embeddings_data["embeddings"]["float"]) == 0:
            return Service_Response_Model(data=[], is_success=False, message="Cannot fetch vector embeddings")
        return Service_Response_Model(data=embeddings_data["embeddings"]["float"][0], is_success=True)
    except Exception as e:
        log_error("Error generating vector embedding document payload: {data}, due to {error}",data=data, error=str(e) )
        raise HTTPException(status_code=500, detail=f"Error generating vector: {str(e)}")



