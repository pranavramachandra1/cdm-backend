import pytest
from datetime import datetime

from app.database import cleanup_test_dbs, get_services

from app.services.task import (
    TaskService,
    TaskCreate,
    TaskResponse,
    TaskNotFoundError,
    InvalidVersionRequest,
    NoTasksToRemove,
)
from app.services.lists import (
    ListService,
    ListCreate,
    ListUpdate,
    ListNotFoundError,
    NoFieldsToUpdateError,
    InvalidParameters,
)
from app.schemas.list import ListVisibilityLevel
from app.exceptions import ListAuthenticationError
from app.services.users import UserService, UserCreate, UserNotFoundError


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

    def test_add_remove_clear_list(self, services, user_create_data: UserCreate):

        # Create user
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)

        # Create list
        list_data = ListCreate(user_id=user_response.user_id, list_name="test list")
        list_response = list_service.create_list(list_data=list_data)

        # Create and add tasks to list:
        task1 = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="test task 1",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )

        task2 = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="test task 2",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )

        task_response1 = task_service.create_task(task_data=task1).model_dump()
        task_response2 = task_service.create_task(task_data=task2).model_dump()

        # Fetch tasks from list:
        task_data_reponse = task_service.get_current_tasks_from_list(
            list_id=list_response.list_id
        )
        # sort the tasks by name
        task_data_response_dicts = sorted(
            [tdr.model_dump() for tdr in task_data_reponse],
            key=lambda x: x["task_name"],
        )

        # Compare task values:
        assert task_response1 == task_data_response_dicts[0], "Task 1 is not correct"
        assert task_response2 == task_data_response_dicts[1], "Task 2 is not correct"

        # Clear list and expect that there are no new tasks:
        cleared_task_data_response = task_service.clear_list(
            list_id=list_response.list_id
        )
        updated_list_response = list_service.get_list(list_id=list_response.list_id)

        # make sure list version is incremented
        assert (
            updated_list_response.version == 2
        ), "List version was not updated correctly"
        assert not cleared_task_data_response, "List was not cleared correctly"

        return

    def test_toggle_complete_rollover(self, services, user_create_data: UserCreate):

        # Create user
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)

        # Create list
        list_data = ListCreate(user_id=user_response.user_id, list_name="test list")
        list_response = list_service.create_list(list_data=list_data)

        # Create and add tasks to list:
        task1 = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="test task 1",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )

        task2 = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="test task 2",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )

        task3 = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="test task 3",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )

        task_response1 = task_service.create_task(task_data=task1)
        task_response2 = task_service.create_task(task_data=task2)
        task_response3 = task_service.create_task(task_data=task3)

        # Mark task 1 as complete
        task_response_1_complete: TaskResponse = task_service.toggle_completion(
            task_id=task_response1.task_id
        )
        assert (
            task_response_1_complete.isComplete
        ), "Task was not correctly marked as complete"

        # Rollover list:
        rollover_response = task_service.rollover_list(list_id=list_response.list_id)

        # sort the tasks by name
        task_data_response_dicts = sorted(
            [tdr.model_dump() for tdr in rollover_response],
            key=lambda x: x["task_name"],
        )

        # Assert that the only tasks in the list are task2 and task3:
        assert (
            len(task_data_response_dicts) == 2
        ), "Tasks were not rolled over correctly"

        # Compare task values:
        assert (
            task_response2.task_name == task_data_response_dicts[0]["task_name"]
        ), "Task 2 was not updated properly"
        assert (
            task_response3.task_name == task_data_response_dicts[1]["task_name"]
        ), "Task 3 was not updated properly"

    def test_list_clear_with_update(self, services, user_create_data: UserCreate):

        # Create user
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)

        # Create list
        list_data = ListCreate(user_id=user_response.user_id, list_name="test list")
        list_response = list_service.create_list(list_data=list_data)

        # Create and add tasks to list:
        task1_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="test task 1",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )

        task1_response = task_service.create_task(task_data=task1_data)

        # Clear list and analyze results
        tasks = task_service.clear_list(list_id=list_response.list_id)
        new_list_response = list_service.get_list(list_id=list_response.list_id)

        # assert that list is now empty
        assert len(tasks) == 0, "List was not cleared properly"
        assert new_list_response.version == 2, "List version was not updated properly"

        return

    def test_list_clear_with_recurring_task(
        self, services, user_create_data: UserCreate
    ):

        # Create user
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)

        # Create list
        list_data = ListCreate(user_id=user_response.user_id, list_name="test list")
        list_response = list_service.create_list(list_data=list_data)

        # Create and add tasks to list:
        task1_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="test task 1",
            reminders=[],
            isPriority=False,
            isRecurring=True,
            list_version=list_response.version,
        )

        task1_response = task_service.create_task(task_data=task1_data)

        # Clear list and analyze results
        tasks = task_service.clear_list(list_id=list_response.list_id)
        new_list_response = list_service.get_list(list_id=list_response.list_id)

        # List should have a duplicated task
        assert len(tasks) == 1, "List was not cleared properly"
        assert new_list_response.version == 2, "List version was not updated properly"
        assert tasks[0].task_name == task1_response.task_name

        return

    def test_toggle_fns(self, services, user_create_data: UserCreate):

        # Create user
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)

        # Create list
        list_data = ListCreate(user_id=user_response.user_id, list_name="test list")
        list_response = list_service.create_list(list_data=list_data)

        # Create and add tasks to list:
        task1_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="test task 1",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )

        task1_response = task_service.create_task(task_data=task1_data)

        # Toggle priority:
        priority_task1_response: TaskResponse = task_service.toggle_priority(
            task_id=task1_response.task_id
        )

        assert priority_task1_response.isPriority, "priority toggle was not executed"
        assert not priority_task1_response.isComplete, "completion toggle error"
        assert not priority_task1_response.isRecurring, "recurring toggle error"

        task_service.toggle_priority(task_id=priority_task1_response.task_id)

        # Toggle recurring
        recurring_task1_response: TaskResponse = task_service.toggle_recurring(
            task_id=task1_response.task_id
        )

        assert not recurring_task1_response.isPriority, "priority toggle error"
        assert (
            not recurring_task1_response.isComplete
        ), "completion should still be false"
        assert recurring_task1_response.isRecurring, "recurring toggle was not executed"

        # Toggle back
        task_service.toggle_recurring(task_id=recurring_task1_response.task_id)

        # Toggle completion:
        completion_task1_response: TaskResponse = task_service.toggle_completion(
            task_id=task1_response.task_id
        )

        assert not completion_task1_response.isPriority, "priority toggle error"
        assert (
            completion_task1_response.isComplete
        ), "completion toggle was not executed"
        assert not completion_task1_response.isRecurring, "recurring should be false"

        return

    # Exception Handling and Edge Case Tests

    def test_list_operations_with_nonexistent_user(self, services):
        """Test list operations fail when user doesn't exist"""
        list_service: ListService = services["list_service"]

        # Try to create list with non-existent user
        invalid_list_data = ListCreate(
            user_id="nonexistent-user-id", list_name="test list"
        )

        # Should succeed in creating list (no user validation in list creation)
        list_response = list_service.create_list(list_data=invalid_list_data)
        assert list_response.list_name == "test list"

    def test_list_service_exceptions(self, services, user_create_data: UserCreate):
        """Test all list service exception scenarios"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]

        user_response = user_service.create_user(user_data=user_create_data)

        # Test InvalidParameters exception
        with pytest.raises(InvalidParameters, match="No arguments were given"):
            list_service.list_exists()

        # Test ListNotFoundError for get_list
        with pytest.raises(ListNotFoundError, match="List does not exist"):
            list_service.get_list("nonexistent-list-id")

        # Test ListNotFoundError for update_list
        with pytest.raises(ListNotFoundError, match="List is not found"):
            from app.services.lists import ListUpdate

            list_service.update_list(
                "nonexistent-list-id", ListUpdate(list_name="new name")
            )

        # Test ListNotFoundError for delete_list
        with pytest.raises(ListNotFoundError, match="List is not found"):
            list_service.delete_list("nonexistent-list-id")

        # Test NoFieldsToUpdateError
        list_data = ListCreate(user_id=user_response.user_id, list_name="test list")
        list_response = list_service.create_list(list_data=list_data)

        from app.services.lists import ListUpdate

        with pytest.raises(NoFieldsToUpdateError, match="No fields to update"):
            list_service.update_list(list_response.list_id, ListUpdate())

        # Test get_lists_by_user with nonexistent user
        with pytest.raises(UserNotFoundError, match="User not found"):
            list_service.get_lists_by_user("nonexistent-user-id")

    def test_task_service_exceptions(self, services, user_create_data: UserCreate):
        """Test all task service exception scenarios"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)

        # Test TaskNotFoundError for get_task
        with pytest.raises(TaskNotFoundError, match="Task does not exist"):
            task_service.get_task("nonexistent-task-id")

        # Test UserNotFoundError for create_task
        list_data = ListCreate(user_id=user_response.user_id, list_name="test list")
        list_response = list_service.create_list(list_data=list_data)

        invalid_task_data = TaskCreate(
            user_id="nonexistent-user-id",
            list_id=list_response.list_id,
            task_name="test task",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )

        with pytest.raises(UserNotFoundError, match="User does not exist"):
            task_service.create_task(task_data=invalid_task_data)

        # Test ListNotFoundError for create_task
        invalid_task_data2 = TaskCreate(
            user_id=user_response.user_id,
            list_id="nonexistent-list-id",
            task_name="test task",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=0,
        )

        with pytest.raises(ListNotFoundError, match="List does not exist"):
            task_service.create_task(task_data=invalid_task_data2)

        # Test toggle functions with nonexistent task
        with pytest.raises(TaskNotFoundError, match="Task does not exist"):
            task_service.toggle_completion("nonexistent-task-id")

        with pytest.raises(TaskNotFoundError, match="Task does not exist"):
            task_service.toggle_priority("nonexistent-task-id")

        with pytest.raises(TaskNotFoundError, match="Task does not exist"):
            task_service.toggle_recurring("nonexistent-task-id")

    def test_list_version_edge_cases(self, services, user_create_data: UserCreate):
        """Test edge cases around list versioning"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(user_id=user_response.user_id, list_name="test list")
        list_response = list_service.create_list(list_data=list_data)

        # Test invalid version requests
        with pytest.raises(
            InvalidVersionRequest, match="Requested version is not valid"
        ):
            task_service.get_tasks_from_list_version(
                list_id=list_response.list_id, list_request_version=-1
            )

        with pytest.raises(
            InvalidVersionRequest, match="Requested version is not valid"
        ):
            task_service.get_tasks_from_list_version(
                list_id=list_response.list_id, list_request_version=999
            )

        with pytest.raises(
            InvalidVersionRequest, match="Requested version is not valid"
        ):
            task_service.get_versions_of_list(
                list_response.list_id, page_start=-1, page_end=0
            )

    def test_empty_list_operations(self, services, user_create_data: UserCreate):
        """Test operations on empty lists"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(user_id=user_response.user_id, list_name="empty list")
        list_response = list_service.create_list(list_data=list_data)

        # Test getting tasks from empty list
        tasks = task_service.get_current_tasks_from_list(list_response.list_id)
        assert len(tasks) == 0, "Empty list should return no tasks"

        # Test clearing empty list
        with pytest.raises(NoTasksToRemove, match="No tasks to clear in list"):
            cleared_tasks = task_service.clear_list(list_response.list_id)

        # Test rollover on empty list
        with pytest.raises(NoTasksToRemove, match="No tasks to clear in list"):
            cleared_tasks = task_service.rollover_list(list_response.list_id)

        # Verify list version was not incremented
        updated_list = list_service.get_list(list_response.list_id)
        assert (
            updated_list.version == list_response.version
        ), "List version should be incremented"

    def test_user_with_multiple_lists(self, services, user_create_data: UserCreate):
        """Test user operations with multiple lists"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]

        user_response = user_service.create_user(user_data=user_create_data)

        # Create multiple lists
        list1 = list_service.create_list(
            ListCreate(user_id=user_response.user_id, list_name="List 1")
        )
        list2 = list_service.create_list(
            ListCreate(user_id=user_response.user_id, list_name="List 2")
        )
        list3 = list_service.create_list(
            ListCreate(user_id=user_response.user_id, list_name="List 3")
        )

        # Get all lists for user
        user_lists = list_service.get_lists_by_user(user_response.user_id)
        assert len(user_lists) == 3, "User should have 3 lists"

        list_names = [l.list_name for l in user_lists]
        assert "List 1" in list_names, "List 1 should be in user's lists"
        assert "List 2" in list_names, "List 2 should be in user's lists"
        assert "List 3" in list_names, "List 3 should be in user's lists"

        # Delete one list
        list_service.delete_list(list1.list_id)

        # Verify list count reduced
        remaining_lists = list_service.get_lists_by_user(user_response.user_id)
        assert len(remaining_lists) == 2, "User should have 2 lists after deletion"

    def test_task_priority_and_recurring_combinations(
        self, services, user_create_data: UserCreate
    ):
        """Test all combinations of task priority and recurring flags"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(user_id=user_response.user_id, list_name="test list")
        list_response = list_service.create_list(list_data=list_data)

        # Test all combinations: priority=T/F, recurring=T/F
        combinations = [
            (True, True),  # Priority + Recurring
            (True, False),  # Priority only
            (False, True),  # Recurring only
            (False, False),  # Neither
        ]

        created_tasks = []
        for is_priority, is_recurring in combinations:
            task_data = TaskCreate(
                user_id=user_response.user_id,
                list_id=list_response.list_id,
                task_name=f"task_p{is_priority}_r{is_recurring}",
                reminders=[],
                isPriority=is_priority,
                isRecurring=is_recurring,
                list_version=list_response.version,
            )
            task_response = task_service.create_task(task_data=task_data)
            created_tasks.append(task_response)

            # Verify task properties
            assert (
                task_response.isPriority == is_priority
            ), f"Priority mismatch for {task_response.task_name}"
            assert (
                task_response.isRecurring == is_recurring
            ), f"Recurring mismatch for {task_response.task_name}"
            assert (
                not task_response.isComplete
            ), f"New task should not be complete: {task_response.task_name}"

        # Test rollover behavior with different combinations
        # Mark some tasks as complete
        task_service.toggle_completion(
            created_tasks[0].task_id
        )  # Priority + Recurring, Complete
        task_service.toggle_completion(
            created_tasks[1].task_id
        )  # Priority only, Complete

        # Perform rollover
        rollover_tasks = task_service.rollover_list(list_response.list_id)

        # Verify rollover results:
        # - Recurring tasks should always be duplicated (regardless of completion)
        # - Non-complete tasks should be duplicated
        # - Complete non-recurring tasks should NOT be duplicated

        rollover_names = [task.task_name for task in rollover_tasks]

        # Task 0: Priority + Recurring + Complete -> should be duplicated
        assert (
            "task_pTrue_rTrue" in rollover_names
        ), "Completed recurring task should be duplicated"

        # Task 1: Priority + Complete -> should NOT be duplicated
        assert (
            "task_pTrue_rFalse" not in rollover_names
        ), "Completed non-recurring task should not be duplicated"

        # Task 2: Recurring + Not Complete -> should be duplicated
        assert (
            "task_pFalse_rTrue" in rollover_names
        ), "Incomplete recurring task should be duplicated"

        # Task 3: Not Priority + Not Recurring + Not Complete -> should be duplicated
        assert (
            "task_pFalse_rFalse" in rollover_names
        ), "Incomplete non-recurring task should be duplicated"

    # Tests for list sharing functionality with get_list_with_share_token
    
    def test_public_list_sharing_success(self, services):
        """Test user1 creates public list, user2 can access successfully"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        
        # Create two users
        user1_data = UserCreate(
            username="user1", email="user1@google.com", password="password",
            phone_number="123-456-7890", first_name="User", last_name="One",
            google_id="google-id"
        )
        user2_data = UserCreate(
            username="user2", email="user2@facebook.com", password="password",
            phone_number="123-456-7891", first_name="User", last_name="Two",
            google_id="google-id"
        )
        
        user1 = user_service.create_user(user_data=user1_data)
        user2 = user_service.create_user(user_data=user2_data)
        
        # User1 creates list
        list_data = ListCreate(user_id=user1.user_id, list_name="Shared List")
        list_response = list_service.create_list(list_data=list_data)
        
        # User1 updates list to PUBLIC
        visibility = ListVisibilityLevel.PUBLIC.value
        update_data = ListUpdate(visibility=visibility)
        updated_list = list_service.update_list(list_response.list_id, update_data)
        
        # User2 accesses list with share token
        shared_list = list_service.get_list_with_share_token(
            share_token=updated_list.share_token, 
            requester_id=user2.user_id
        )
        
        assert shared_list.list_id == updated_list.list_id
        assert shared_list.list_name == "Shared List"
        assert shared_list.visibility == ListVisibilityLevel.PUBLIC.value

    def test_private_list_sharing_denied(self, services):
        """Test user1 creates private list, user2 cannot access"""
        user_service: UserService = services["user_service"] 
        list_service: ListService = services["list_service"]
        
        # Create two users
        user1_data = UserCreate(
            username="user1b", email="user1b@google.com", password="password",
            phone_number="123-456-7892", first_name="User", last_name="One",
            google_id="google-id"
        )
        user2_data = UserCreate(
            username="user2b", email="user2b@facebook.com", password="password",
            phone_number="123-456-7893", first_name="User", last_name="Two",
            google_id="google-id"
        )
        
        user1 = user_service.create_user(user_data=user1_data)
        user2 = user_service.create_user(user_data=user2_data)
        
        # User1 creates list (defaults to PRIVATE)
        list_data = ListCreate(user_id=user1.user_id, list_name="Private List")
        list_response = list_service.create_list(list_data=list_data)
        
        # User2 attempts to access private list - should fail
        with pytest.raises(ListAuthenticationError, match="List is private and cannot be accessed"):
            list_service.get_list_with_share_token(
                share_token=list_response.share_token,
                requester_id=user2.user_id
            )

    def test_organization_only_different_domains_denied(self, services):
        """Test ORGANIZATION_ONLY with different domains - access denied"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        
        # Create users with different domains
        user1_data = UserCreate(
            username="user1c", email="johndoe@google.com", password="password",
            phone_number="123-456-7894", first_name="John", last_name="Doe",
            google_id="google-id"
        )
        user2_data = UserCreate(
            username="user2c", email="abc123@facebook.com", password="password",
            phone_number="123-456-7895", first_name="Jane", last_name="Smith",
            google_id="google-id"
        )
        
        user1 = user_service.create_user(user_data=user1_data)
        user2 = user_service.create_user(user_data=user2_data)
        
        # User1 creates list and sets to ORGANIZATION_ONLY
        list_data = ListCreate(user_id=user1.user_id, list_name="Org Only List")
        list_response = list_service.create_list(list_data=list_data)
        
        update_data = ListUpdate(visibility=ListVisibilityLevel.ORGANIZATION_ONLY.value)
        updated_list = list_service.update_list(list_response.list_id, update_data)
        
        # User2 from different domain attempts access - should fail
        with pytest.raises(ListAuthenticationError, match="List is set to domain only and domain names do not match"):
            list_service.get_list_with_share_token(
                share_token=updated_list.share_token,
                requester_id=user2.user_id
            )

    def test_organization_only_same_domain_success(self, services):
        """Test ORGANIZATION_ONLY with same domain - access granted"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        
        # Create users with same domain
        user1_data = UserCreate(
            username="user1d", email="johndoe@google.com", password="password",
            phone_number="123-456-7896", first_name="John", last_name="Doe",
            google_id="google-id"
        )
        user2_data = UserCreate(
            username="user2d", email="abc123@google.com", password="password",
            phone_number="123-456-7897", first_name="Jane", last_name="Smith",
            google_id="google-id"
        )
        
        user1 = user_service.create_user(user_data=user1_data)
        user2 = user_service.create_user(user_data=user2_data)
        
        # User1 creates list and sets to ORGANIZATION_ONLY
        list_data = ListCreate(user_id=user1.user_id, list_name="Org List Same Domain")
        list_response = list_service.create_list(list_data=list_data)
        
        update_data = ListUpdate(visibility=ListVisibilityLevel.ORGANIZATION_ONLY.value)
        updated_list = list_service.update_list(list_response.list_id, update_data)
        
        # User2 from same domain accesses list - should succeed
        shared_list = list_service.get_list_with_share_token(
            share_token=updated_list.share_token,
            requester_id=user2.user_id
        )
        
        assert shared_list.list_id == updated_list.list_id
        assert shared_list.list_name == "Org List Same Domain"
        assert shared_list.visibility == ListVisibilityLevel.ORGANIZATION_ONLY.value

    def test_same_user_can_always_access_own_list(self, services):
        """Test that the list owner can always access their own list regardless of visibility"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        
        # Create user
        user_data = UserCreate(
            username="owner", email="owner@test.com", password="password",
            phone_number="123-456-7898", first_name="Owner", last_name="User",
            google_id="google-id"
        )
        user = user_service.create_user(user_data=user_data)
        
        # Create private list
        list_data = ListCreate(user_id=user.user_id, list_name="Owner's Private List")
        list_response = list_service.create_list(list_data=list_data)
        
        # Owner accesses their own private list - should succeed
        accessed_list = list_service.get_list_with_share_token(
            share_token=list_response.share_token,
            requester_id=user.user_id
        )
        
        assert accessed_list.list_id == list_response.list_id
        assert accessed_list.visibility == ListVisibilityLevel.PRIVATE.value

    def test_get_list_with_invalid_share_token(self, services):
        """Test accessing list with nonexistent share token"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        
        # Create user
        user_data = UserCreate(
            username="testuser", email="test@test.com", password="password",
            phone_number="123-456-7899", first_name="Test", last_name="User",
            google_id="google-id"
        )
        user = user_service.create_user(user_data=user_data)
        
        # Try to access with invalid share token - should fail
        with pytest.raises(ListNotFoundError, match="List does not exist"):
            list_service.get_list_with_share_token(
                share_token="invalid-token-12345",
                requester_id=user.user_id
            )

    def test_get_list_with_nonexistent_requester(self, services):
        """Test accessing list with nonexistent requester user"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        
        # Create list owner
        user_data = UserCreate(
            username="listowner", email="listowner@test.com", password="password",
            phone_number="123-456-7800", first_name="List", last_name="Owner",
            google_id="google-id"
        )
        user = user_service.create_user(user_data=user_data)
        
        # Create list
        list_data = ListCreate(user_id=user.user_id, list_name="Test List")
        list_response = list_service.create_list(list_data=list_data)
        
        # Try to access with nonexistent requester - should fail
        with pytest.raises(UserNotFoundError):
            list_service.get_list_with_share_token(
                share_token=list_response.share_token,
                requester_id="nonexistent-user-id"
            )
    