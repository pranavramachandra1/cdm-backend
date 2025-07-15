import pytest
from datetime import datetime

from app.database import cleanup_test_dbs, get_services

from app.services.task import TaskService, TaskCreate
from app.services.lists import ListService, ListCreate
from app.services.users import UserService, UserCreate

class TestListOperations:
    """
    Testing CRUD functionalities for CRUD operations
    related to users
    """

    @pytest.fixture(scope="session", autouse=True)  # Add autouse=True
    def cleanup(self):
        yield
        cleanup_test_dbs()

    @pytest.fixture
    def user_create_data(self):
        return UserCreate(
            username="johndoe123",
            email="johndoe123@gmail.com",
            password="password",
            phone_number="(847)-732-0621",
            first_name="John",
            last_name="Doe",
            google_id="google-id",
        )
    
    @pytest.fixture
    def services(self):
        return get_services()
    
    def test_add_remove_clear_list(self, services,
                                   user_create_data: UserCreate):

        # Create user
        user_service: UserService = services['user_service']
        list_service: ListService = services['list_service']
        task_service: TaskService = services['task_service']

        user_response = user_service.create_user(user_data = user_create_data)

        # Create list
        list_data = ListCreate(
            user_id = user_response.user_id,
            list_name = "test list"
        )
        list_response = list_service.create_list(
            list_data=list_data
        )

        # Create and add tasks to list:
        task1 = TaskCreate(
            user_id = user_response.user_id,
            list_id = list_response.list_id,
            task_name = "test task 1",
            reminders = [],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version
        )

        task2 = TaskCreate(
            user_id = user_response.user_id,
            list_id = list_response.list_id,
            task_name = "test task 2",
            reminders = [],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version
        )

        task_response1 = task_service.create_task(task_data = task1).model_dump()
        task_response2 = task_service.create_task(task_data = task2).model_dump()
        

        # Fetch tasks from list:
        task_data_reponse = task_service.get_current_tasks_from_list(list_id = list_response.list_id)
        # sort the tasks by name
        task_data_response_dicts = sorted([tdr.model_dump() for tdr in task_data_reponse], key = lambda x: x['task_name'])
        
        # Compare task values:
        assert task_response1 == task_data_response_dicts[0], "Task 1 is not correct"
        assert task_response2 == task_data_response_dicts[1], "Task 2 is not correct"

        # Clear list and expect that there are no new tasks:
        cleared_task_data_response = task_service.clear_list(list_id = list_response.list_id)
        updated_list_response = list_service.get_list(list_id = list_response.list_id)
        
        # make sure list version is incremented
        assert updated_list_response.version == 1, "List version was not updated correctly"
        assert not cleared_task_data_response, "List was not cleared correctly"
        
        return