from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.server_api import ServerApi
from functools import lru_cache
import os
from datetime import datetime
import random

from app.services.users import UserService
from app.services.lists import ListService
from app.services.task import TaskService

from app.dependencies import TEST_ENV, get_mongo_db

def get_test_collection(name):
    """
    Creates a test collection
    """
    db = get_mongo_db()
    return db.create_collection(
        name=f"test-{name}-{datetime.now().isoformat()}-{random.randint(0, 999999):06d}"
    )

def get_test_user_service():
    """
    Creates a temporary user service collection for testing
    """
    user_collection = get_test_collection("user-collection")
    return UserService(user_collection)

def get_test_list_service():
    """
    Creates a temporary list service collection for testing
    """
    list_collection = get_test_collection("list-collection")
    user_collection = get_test_collection("user-collection")
    return ListService(list_collection=list_collection, user_collection=user_collection)

def get_test_task_service():
    """
    Creates a temporary task service collection for testing
    """
    list_collection = get_test_collection("list-collection")
    user_collection = get_test_collection("user-collection")
    task_collection = get_test_collection("task-collection")
    return TaskService(task_collection=task_collection, user_collection=user_collection, list_collection=list_collection)

async def cleanup_service(service):
    """
    Deletes all MongoDB collections for a given service
    """
    if isinstance(service, (UserService, ListService, TaskService)):
        await delete_test_collection(service.user_collection)

    if isinstance(service, (ListService, TaskService)):
        await delete_test_collection(service.list_collection)

    if isinstance(service, TaskService):
        await delete_test_collection(service.task_collection)

async def delete_test_collection(collection):
    """
    Deletes the collection from the db
    """
    db = get_mongo_db()
    try:
        db.drop_collection(collection)
    except Exception as e:
        raise Exception(f"Failed to drop collection: {e}")
    return {"message": "drop successful"}

async def cleanup(user_service=None, list_service=None, task_service=None):
    """
    Wrapper function that cleans up all testing DBs
    """
    breakpoint()  # This should now be reached
    if user_service:
        await cleanup_service(user_service)
    if list_service:
        await cleanup_service(list_service)
    if task_service:
        await cleanup_service(task_service)