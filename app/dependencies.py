from pymongo import MongoClient
from pymongo.collection import Collection
from functools import lru_cache
import os
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

from app.services.users import UserService
from app.services.lists import ListService
from app.services.task import TaskService

TEST_ENV = "TEST"

client = MongoClient()
load_dotenv()


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

    breakpoint()

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

    breakpoint()

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

if __name__ == "__main__":

    breakpoint()