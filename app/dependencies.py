from pymongo import MongoClient
from pymongo.collection import Collection
from functools import lru_cache
import os
from pymongo.server_api import ServerApi

client = MongoClient()


@lru_cache
def get_mongo_db():
    """Get MongoDB client - cached for performance"""
    # Collect environment Variables
    mongo_password = os.getenv("MONGO_DB_PASSWORD")
    mongo_username = os.getenv("MONGO_DB_USERNAME")

    # grab mongo client & db
    mongo_url = MongoClient(
        f"mongodb+srv://{mongo_username}:{mongo_password}@cluster0.3qeyv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
        server_api=ServerApi("1"),
    )
    db = mongo_url.todov2

    # Return DB
    return db


@lru_cache
def get_user_collection():
    """Gets the user collections from db"""
    db = get_mongo_db()

    breakpoint()

    return db["test-users"] if os.getenv("ENV") == "TEST" else db["prod-users"]


@lru_cache
def get_list_collection():
    """Gets the list collections from db"""

    db = get_mongo_db()
    return db["test-lists"] if os.getenv("ENV") == "TEST" else db["prod-lists"]


@lru_cache
def get_list_collection():
    """Gets the task collections from db"""
    db = get_mongo_db()

    return db["test-tasks"] if os.getenv("ENV") == "TEST" else db["prod-tasks"]
