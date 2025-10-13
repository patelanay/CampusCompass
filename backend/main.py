
#loads mongo db atlas client and connects to the database
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
#loads .env file which contains the connection uri and password
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
uri = os.getenv("MONGODB_URI")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


###Test insert something

db = client["sample_database"]
collection = db["sample_collection"]

# sample document
sample_doc = {
    "name": "John cena",
    "email": "Jcena@email.com",
    "age": 59
}

# Insert the document
result = collection.insert_one(sample_doc)
print(f"Inserted document with _id: {result.inserted_id}")

# Retrieve the document by a field (e.g., name)
retrieved_doc = collection.find_one({"name": "John Doe"})
print("Retrieved document:", retrieved_doc)