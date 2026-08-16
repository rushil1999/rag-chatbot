import app.env  # noqa: F401  (loads .env before anything reads os.getenv)
import httpx

from fastapi import HTTPException
import os
from app.service.logging import log_info, log_error
from app.models.response_models import Service_Response_Model


# Reused async client keeps connections alive (avoids per-call TLS handshake)
_async_client = httpx.AsyncClient(timeout=30.0)

# Function to get the API key from the environment
def get_api_key():
    return os.getenv("COHERE_EMBEDDING_API_KEY")

async def generate_vector_embeddings(input: str, input_type: str = "search_query"):
    log_info("Embedding {length} chars as {input_type}", length=len(input), input_type=input_type)
    data = None
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
            "input_type": input_type,
            "embedding_types": ["float"]
        }
        response = await _async_client.post(url, json=data, headers=headers)
        if response.status_code != httpx.codes.OK:
            # Bail out here — continuing would blow up on the missing "embeddings" key and
            # surface as an opaque 500 instead of a handled failure.
            log_error(
                "Error fetching data from Cohere API, status code: {status_code}",
                status_code=response.status_code,
            )
            return Service_Response_Model(
                data=[],
                is_success=False,
                status_code=502,
                message="Cannot fetch vector embeddings",
            )

        embeddings_data = response.json()
        floats = (embeddings_data.get("embeddings") or {}).get("float") or []
        if len(floats) == 0:
            log_error("Cohere API returned no embeddings")
            return Service_Response_Model(data=[], is_success=False, message="Cannot fetch vector embeddings")
        log_info("Generated embedding of {dimensions} dimensions", dimensions=len(floats[0]))
        return Service_Response_Model(data=floats[0], is_success=True)
    except Exception as e:
        log_error("Error generating vector embedding: {error}", error=str(e))
        raise HTTPException(status_code=500, detail="Error generating vector embedding")
