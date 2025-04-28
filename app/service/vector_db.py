
import asyncio
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi



uri = "mongodb+srv://rushil1999:MongoDB1999%40@rushhour.seknofy.mongodb.net/?retryWrites=true&w=majority&appName=RushHour"
# Create a new client and connect to the server
vector_store = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)