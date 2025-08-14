import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import uuid
from pydantic import BaseModel
from typing import Optional, List
from passlib.context import CryptContext
from datetime import datetime

from app.services.users import UserService
from app.schemas.list import ListCreate, ListUpdate, ListResponse

# Use centralized exceptions
from app.exceptions import (
    ListNotFoundError,
    NoFieldsToUpdateError,
    FailedToDeleteList,
    InvalidParameters,
)
from app.exceptions.user import UserNotFoundError

# Exception Handling:


class ListService:
    def __init__(self, list_collection=None, user_collection=None):
        self.list_collection = list_collection
        self.user_service = (
            UserService(user_collection=user_collection)
            if user_collection is not None
            else UserService()
        )

    @staticmethod
    def create_list_id() -> str:
        return str(uuid.uuid4())

    def list_exists(
        self, user_id: str = None, list_name: str = None, list_id: str = None
    ) -> bool:
        """
        Checks if a list already exists with the same name for a given user
        """
        # first check if list_id is passed through
        if list_id:
            query_conditions = {"list_id": list_id}
        # use, use user_id and list_name to check if name exists in user's set of lists
        elif user_id and list_name:
            query_conditions = {"user_id": user_id, "list_name": list_name}
        else:
            raise InvalidParameters("No arguments were given")

        result = self.list_collection.find_one(query_conditions)

        # return if result is None or not
        return True if result else False

    def create_list(self, list_data: ListCreate) -> ListResponse:
        """
        Creates a new list, assumes user exists
        """

        # create list document
        list_id = self.create_list_id()

        list_doc = {
            "list_id": list_id,
            "user_id": list_data.user_id,
            "list_name": list_data.list_name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": 1,
        }

        self.list_collection.insert_one(list_doc)

        # Return list object:
        return ListResponse(**list_doc)

    def update_list(self, list_id: str, list_data: ListUpdate):
        """
        Updates a list
        """

        # check if list exists
        if not self.list_exists(list_id=list_id):
            raise ListNotFoundError("List is not found")

        # Get fields which were provided:
        update_data = list_data.model_dump(exclude_unset=True)

        if not update_data:
            raise NoFieldsToUpdateError("No fields to update")

        update_data["last_updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # update in DB:
        self.list_collection.update_one({"list_id": list_id}, {"$set": update_data})

        # return list
        return self.get_list(list_id)

    def get_list(self, list_id: str) -> ListResponse:
        """
        Retrieves list by ID
        """

        # fetch list from DB
        list_response = self.list_collection.find_one({"list_id": list_id})

        if not list_response:
            raise ListNotFoundError("List does not exist")

        # return response
        return ListResponse(**list_response)

    def delete_list(self, list_id: str):
        """
        Deletes a list by ID
        """

        # check if list exists
        if not self.list_exists(list_id=list_id):
            raise ListNotFoundError("List is not found")

        result = self.list_collection.delete_one({"list_id": list_id})

        if result.deleted_count == 0:
            raise FailedToDeleteList("Failed to delete list")

        return {"message": "List deleted successfully"}

    def get_lists_by_user(self, user_id: str) -> List[ListResponse]:
        """
        Get's all the list_ids from a single user_id
        """
        # check if user exists:
        if not self.user_service.user_exists(user_id=user_id):
            raise UserNotFoundError("User not found")

        list_response = list(self.list_collection.find({"user_id": user_id}))

        # convert each response to the base model
        formatted_output = [ListResponse(**l) for l in list_response]

        # return the output:
        return formatted_output

    def increment_version(self, list_id: str) -> ListResponse:
        """
        Increments the version of a list by 1.

        A list's version is incremented when a list is either cleared or rolled-over.
        This will maintain the task history for a given list.
        """

        # Get list:
        current_list = self.get_list(list_id)

        # Update List's Version:
        updated_list = ListUpdate(version=current_list.version + 1)

        # Update list:
        self.update_list(list_id=list_id, list_data=updated_list)

        # Return List:
        return self.get_list(list_id)
