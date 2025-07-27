from fastapi import Header, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pymongo import MongoClient
from pymongo.collection import Collection
from functools import lru_cache
import os
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

from app.services.users import UserService
from app.services.lists import ListService
from app.services.task import TaskService

load_dotenv()

TEST_ENV = "TEST"
X_API_KEY = os.getenv("API_KEY")
MONGO_PASSWORD = os.getenv("MONGO_DB_PASSWORD")
MONGO_USERNAME = os.getenv("MONGO_DB_USERNAME")

if not X_API_KEY:
    raise ValueError("API_KEY environment variable must be set")
if not MONGO_PASSWORD or not MONGO_USERNAME:
    raise ValueError("MongoDB credentials must be set")


@lru_cache
def get_mongo_db():
    """Get MongoDB client - cached for performance"""

    # grab mongo client & db
    mongo_url = MongoClient(
        f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@cluster0.3qeyv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
        server_api=ServerApi("1"),
    )

    # Return DB
    return mongo_url.todov2


@lru_cache
def get_user_service() -> UserService:
    """Serves UserService"""
    # Fetch db
    db = get_mongo_db()

    # Fetch user collection
    user_collection = (
        db["test-users"] if os.getenv("ENV") == TEST_ENV else db["prod-users"]
    )

    return UserService(user_collection=user_collection)


@lru_cache
def get_list_service() -> ListService:
    """Serves list service"""
    # Fetch db
    db = get_mongo_db()

    # Fetch user and list collections:
    user_collection = (
        db["test-users"] if os.getenv("ENV") == TEST_ENV else db["prod-users"]
    )
    list_collection = (
        db["test-lists"] if os.getenv("ENV") == TEST_ENV else db["prod-lists"]
    )

    return ListService(list_collection=list_collection, user_collection=user_collection)


@lru_cache
def get_task_service() -> TaskService:
    """Serves task service"""
    db = get_mongo_db()

    # Fetch user, list and task collections:
    user_collection = (
        db["test-users"] if os.getenv("ENV") == TEST_ENV else db["prod-users"]
    )
    list_collection = (
        db["test-lists"] if os.getenv("ENV") == TEST_ENV else db["prod-lists"]
    )
    task_collection = (
        db["test-tasks"] if os.getenv("ENV") == TEST_ENV else db["prod-tasks"]
    )

    return TaskService(
        user_collection=user_collection,
        list_collection=list_collection,
        task_collection=task_collection,
    )


def get_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Validate API key from X-API-Key header"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")

    if x_api_key != X_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key


# Alternative using APIKeyHeader (more explicit)
api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key_alt(api_key: str = Depends(api_key_header)):
    """Alternative API key validation using APIKeyHeader"""
    if api_key != X_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key
