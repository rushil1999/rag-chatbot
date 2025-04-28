import httpx

from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Function to get the API key from the environment
def get_api_key():
    return os.getenv("COHERE_EMBEDDING_API_KEY")

async def generate_vector_embeddings(input: str):

    # return {"data": input}
    
    key = get_api_key()
    print("Received Input", input, key)
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
    print("Called the API", data, headers)
    if response.status_code == httpx.codes.OK :
        print(response.json())
    else:
        print("Error, got status", response.status_code)
    embeddings_data = response.json()
    # print("Output", embeddings_data, embeddings_data["embeddings"]["float"])
    return embeddings_data["embeddings"]["float"]



