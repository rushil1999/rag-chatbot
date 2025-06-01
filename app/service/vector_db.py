
import asyncio
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()

uri = os.getenv("MONGODB_URI")
# Create a new client and connect to the server
vector_store = MongoClient(uri, server_api=ServerApi('1'))
vector_db = vector_store['personal_assisstant_chat']
vector_collection = vector_db['data_embeddings']
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)