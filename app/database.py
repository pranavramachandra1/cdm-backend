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


def get_services():
    """Creates a temporary user, list, and task collection for testing"""
    user_collection = get_test_collection("user_collection")
    list_collection = get_test_collection("list_collection")
    task_collection = get_test_collection("task_collection")

    return {
        "user_service": UserService(user_collection=user_collection),
        "list_service": ListService(
            user_collection=user_collection, list_collection=list_collection
        ),
        "task_service": TaskService(
            user_collection=user_collection,
            list_collection=list_collection,
            task_collection=task_collection,
        ),
    }


def cleanup_test_dbs():
    """
    Deletes all test collections created in db

    It is hardcoded, definitely not the best practice, but would love
    to see how it should be done.
    """

    db = get_mongo_db()

    for collection in db.list_collections():
        if "test-" in collection["name"]:
            db.drop_collection(collection["name"])
