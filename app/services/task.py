import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import uuid
from pydantic import BaseModel, field_validator, ValidationInfo
from typing import Optional
from passlib.context import CryptContext
from typing import List

from app.services.users import UserService, UserNotFoundError
from app.services.lists import ListService, ListNotFoundError

# Pydantic Models:


class TaskCreate(BaseModel):
    user_id: str
    list_id: str
    task_name: str
    reminders: List[datetime]
    isPriority: bool
    isRecurring: bool
    list_version: int


class TaskUpdate(BaseModel):
    user_id: Optional[str] = None
    list_id: Optional[str] = None
    task_id: Optional[str] = None
    task_name: Optional[str] = None
    reminders: Optional[List[datetime]] = None
    isComplete: Optional[bool] = None
    isPriority: Optional[bool] = None
    isRecurring: Optional[bool] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    list_version: Optional[int] = None


class TaskResponse(BaseModel):
    user_id: str
    list_id: str
    task_id: str
    task_name: str
    reminders: List[datetime]
    isComplete: bool
    isPriority: bool
    isRecurring: bool
    createdAt: datetime
    updatedAt: datetime
    list_version: int


# Exception Handling:
class TaskNotFoundError(Exception):
    pass


class NoFieldsToUpdateError(Exception):
    pass


class FailedToDeleteTaskError(Exception):
    pass


class InvalidVersionRequest(Exception):
    pass

class ToggleIncompleteError(Exception):
    pass

class NoTasksToRemove(Exception):
    pass

class TaskService:

    def __init__(
        self, task_collection=None, user_collection=None, list_collection=None
    ):
        self.task_collection = task_collection

        # Create user service:
        self.user_service = (
            UserService(user_collection=user_collection)
            if user_collection is not None
            else UserService()
        )

        # Create list service
        if user_collection is not None and list_collection is not None:
            self.list_service = ListService(
                list_collection=list_collection, user_collection=user_collection
            )
        else:
            self.list_service = ListService()

    @staticmethod
    def create_task_id() -> str:
        return str(uuid.uuid4())

    def create_task(self, task_data: TaskCreate) -> TaskResponse:
        """
        Creates a task for a given user and list
        """
        # check if user exists:
        if not self.user_service.user_exists(user_id =task_data.user_id):
            raise UserNotFoundError("User does not exist")

        # check if list exists:
        if not self.list_service.list_exists(list_id = task_data.list_id):
            raise ListNotFoundError("List does not exist")

        # create Task document:
        task_id = self.create_task_id()

        task_doc = {
            "user_id": task_data.user_id,
            "list_id": task_data.list_id,
            "task_id": task_id,
            "task_name": task_data.task_name,
            "reminders": task_data.reminders,
            "isComplete": False,
            "isPriority": task_data.isPriority,
            "isRecurring": task_data.isRecurring,
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "list_version": task_data.list_version,
        }

        self.task_collection.insert_one(task_doc)

        return TaskResponse(**task_doc)

    def get_task(self, task_id: str) -> TaskResponse:
        """
        Fetch task from DB
        """

        response = self.task_collection.find_one({"task_id": task_id})

        if not response:
            raise TaskNotFoundError("Task does not exist")

        return TaskResponse(**response)

    def update_task(self, user_id: str, task_id: str, task_data: TaskUpdate):
        """
        Updates task with only relevant fields
        """
        # check if user exists:
        if not self.user_service.user_exists(user_id = user_id):
            raise UserNotFoundError("User does not exist")

        # check if task exists:
        if not self.task_collection.find_one({"task_id": task_id}):
            raise TaskNotFoundError("Task does not exist")

        # Get fields that were provided:
        update_data = task_data.model_dump(exclude_unset=True)

        if not update_data:
            raise NoFieldsToUpdateError("No fields to update")

        # Add timestampe:
        update_data["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # update in DB:
        self.task_collection.update_one({"user_id": user_id}, {"$set": update_data})

        return self.get_task(task_id)

    def delete_task(self, task_id: str) -> dict:
        """
        Deletes a task by ID
        """

        if not self.task_collection.find_one({"task_id": task_id}):
            raise UserNotFoundError("User does not exist")

        result = self.task_collection.delete_one({"task_id": task_id})

        if result.deleted_count == 0:
            raise FailedToDeleteTaskError("Failed to delete task")

        return {"message": "User deleted successfully"}

    def _duplicate_task(self, task_id: str, new_list_version: int) -> TaskResponse:
        """
        Duplicates a task with a new task_id
        """

        # Retrieve task
        task_response = self.get_task(task_id)

        # Duplciate task onto new list version
        new_task = TaskCreate(
            user_id=task_response.user_id,
            list_id=task_response.list_id,
            task_name=task_response.task_name,
            reminders=[],
            isPriority=task_response.isPriority,
            isRecurring=task_response.isRecurring,
            list_version=new_list_version,
        )

        # Create new task
        return self.create_task(new_task)

    def toggle_completion(self, task_id: str) -> dict:
        """
        Updates the completion status of a task
        """

        # Get task
        task = self.get_task(task_id)

        # Toggle activity
        task.isComplete = not task.isComplete
        toggled_task =  TaskUpdate(**task.model_dump())

        # Update Task
        try:
            self.update_task(user_id = task.user_id, 
                             task_id = task.task_id, 
                             task_data = toggled_task)
        except Exception as e:
            return {"message": "Task toggle was not successful"}

        return self.get_task(task_id)
    
    def toggle_recurring(self, task_id: str) -> dict:
        """
        Updates the completion status of a task
        """

        # Get task
        task = self.get_task(task_id)

        # Toggle activity
        task.isRecurring = not task.isRecurring
        toggled_task = TaskUpdate(**task.model_dump())

        # Update Task
        try:
            self.update_task(user_id = task.user_id, 
                             task_id = task.task_id, 
                             task_data = toggled_task)
        except Exception as e:
            return {"message": "Task toggle was not successful"}

        return self.get_task(task_id)
    
    def toggle_priority(self, task_id: str) -> dict:
        """
        Updates the completion status of a task
        """

        # Get task
        task = self.get_task(task_id)

        # Toggle activity
        task.isPriority = not task.isPriority
        toggled_task =  TaskUpdate(**task.model_dump())

        # Update Task
        try:
            self.update_task(user_id = task.user_id, 
                             task_id = task.task_id, 
                             task_data = toggled_task)
        except Exception as e:
            return {"message": "Task toggle was not successful"}

        return self.get_task(task_id)

    def get_current_tasks_from_list(self, list_id: str) -> List[TaskResponse]:
        """
        Retrieves all tasks from a given list_id
        """

        # Get the list:
        list_response = self.list_service.get_list(list_id)

        if list_response is None:
            raise ListNotFoundError("List does not exist")
        
        tasks = list(
            self.task_collection.find(
                {"list_id": list_id, "list_version": list_response.version}
            )
        )

        # convert output to all TasksResponse models and return
        return [TaskResponse(**t) for t in tasks]

    def _get_tasks_from_list_version(
        self, list_id: str, list_version: int
    ) -> List[TaskResponse]:
        """
        Retrieves all tasks from a specified version of a task
        """

        # Check if list exists:
        if not self.list_service.list_exists(list_id):
            raise ListNotFoundError("List does not exist")

        # Get List:
        list_response = self.list_service.get_list(list_id)

        # Check if requested version is valid:
        if list_version < 0 or list_version > list_response.version:
            raise InvalidVersionRequest("Requested version is not valid")

        tasks = list(
            self.task_collection.find(
                {"list_id": list_id}, {"list_version": list_version}
            )
        )

        # convert output to all TasksResponse models and return
        return [TaskResponse(**t) for t in tasks]

    def clear_list(self, list_id: str) -> List[TaskResponse]:
        """
        Clears all current items from todo-list by removing activity label on all tasks
        """

        # Get all tasks from list
        tasks = self.get_current_tasks_from_list(list_id)

        # Raise error if there are no tasks to update:
        if len(tasks) == 0:
            raise NoTasksToRemove("No tasks to clear in list")

        # Update the list with the new version:
        new_list = self.list_service.increment_version(list_id)
        new_list_version = new_list.version

        for task in tasks:

            if task.isRecurring:
                self._duplicate_task(task.task_id, new_list_version)

        return self.get_current_tasks_from_list(list_id)

    def rollover_list(self, list_id: str) -> List[TaskResponse]:
        """
        Clears all tasks that are complete from todo-list, removing activity labesl on all complete tasks
        """

        # Get all tasks from list
        tasks = self.get_current_tasks_from_list(list_id)

        # Raise error if there are no tasks to update:
        if len(tasks) == 0:
            raise NoTasksToRemove("No tasks to clear in list")

        # Update the list with the new version:
        new_list = self.list_service.increment_version(list_id)
        new_list_version = new_list.version

        for task in tasks:
            # Duplicate task if task is recurring
            if task.isRecurring or not task.isComplete:
                self._duplicate_task(task.task_id, new_list_version)

        # Return new list:
        return self.get_current_tasks_from_list(list_id)

    def get_versions_of_list(
        self, list_id: str, page_start: int = 0, page_end: int = 5
    ) -> List[List[TaskResponse]]:
        """
        Returns a paginated account of the previous versions of a to-do list

        Args:
            list_id: str
            page_start: int = the latest version of the list to acquire
            page_end: int = the earliest version of the list to acquire
        """

        list_response = self.list_service.get_list(list_id)
        list_version = list_response.version

        # Check if list version is queryable
        if list_version < 0 or list_version > list_response.version:
            raise InvalidVersionRequest("Requested version(s) are invalid")

        # Gather all responses from DB
        response = []
        for page in range(page_start, page_end):
            response.append(self._get_tasks_from_list_version(list_id, page))

        return response
