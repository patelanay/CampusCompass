"""MongoDB connection helpers for the backend."""

import os
from typing import Optional

from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


def load_env_variables() -> Optional[str]:
    """Load environment variables and return the configured MongoDB URI."""
    load_dotenv()
    return os.getenv("MONGODB_URI")


def create_mongo_client(uri: str) -> MongoClient:
    """Create and validate a MongoDB client by issuing a ping command."""
    if not uri:
        raise ValueError("MONGODB_URI is not set. Check your .env file.")

    client = MongoClient(uri, server_api=ServerApi("1"))
    try:
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return client
    except Exception as exc:
        print(f"Failed to connect to MongoDB: {exc}")
        client.close()
        raise


# Backward-compatible aliases for existing imports.
loadEnvVariables = load_env_variables
createMongoClient = create_mongo_client

