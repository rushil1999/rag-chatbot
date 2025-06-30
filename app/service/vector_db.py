
import asyncio
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from app.service.logging import log_info, log_error
from fastapi import HTTPException

# Load environment variables from .env
load_dotenv()


# Create a new client and connect to the server
uri = os.getenv("MONGODB_URI")
vector_store = MongoClient(uri, server_api=ServerApi('1'))
vector_db = vector_store['personal_assisstant_chat']
vector_collection = vector_db['data_embeddings']

cosine_similarity_threshold = 0.75

cursor = vector_collection.find({"text": "Cosine Similarity Threshold"})
for document in cursor:
    cosine_similarity_threshold = document['value']
    break

# Send a ping to confirm a successful connection
try:
    vector_store.admin.command('ping')
    log_info("Pinged your deployment. You successfully connected to MongoDB!")
    
except Exception as e:
    log_error("Error establishing database connection, {error}", error={str(e)})
    raise HTTPException(status_code=500, detail=f"Error establishing database connection: {str(e)}")
