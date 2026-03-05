#loads mongo db atlas client and connects to the database
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
#loads .env file which contains the connection uri and password
from dotenv import load_dotenv
import os

def loadEnvVariables():
    # Load environment variables from .env file
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    return uri

def createMongoClient(uri):
    if not uri:
        raise ValueError("MONGODB_URI is not set. Check your .env file.")

    client = MongoClient(uri, server_api=ServerApi('1'))

    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        client.close()
        raise

