import app.env  # noqa: F401  (loads .env before anything reads os.getenv)

import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from app.service.logging import log_info, log_error
from fastapi import HTTPException

# Create a new client and connect to the server
uri = os.getenv("MONGODB_URI")
vector_store = MongoClient(uri, server_api=ServerApi('1'))
vector_db = vector_store['personal_assisstant_chat']
vector_collection = vector_db['data_embeddings']

# Threshold precedence: env var, then the legacy config document stored in the embeddings
# collection (kept so existing deployments keep working), then the default.
cosine_similarity_threshold = 0.75

_env_threshold = os.getenv("COSINE_SIMILARITY_THRESHOLD")
if _env_threshold:
    try:
        cosine_similarity_threshold = float(_env_threshold)
    except ValueError:
        log_error("Invalid COSINE_SIMILARITY_THRESHOLD {value}; using default", value=_env_threshold)
else:
    for document in vector_collection.find({"text": "Cosine Similarity Threshold"}):
        cosine_similarity_threshold = document['value']
        break

log_info("Cosine similarity threshold set to {threshold}", threshold=cosine_similarity_threshold)

# Send a ping to confirm a successful connection
try:
    vector_store.admin.command('ping')
    log_info("Pinged your deployment. You successfully connected to MongoDB!")
    
except Exception as e:
    log_error("Error establishing database connection, {error}", error={str(e)})
    raise HTTPException(status_code=500, detail=f"Error establishing database connection: {str(e)}")
