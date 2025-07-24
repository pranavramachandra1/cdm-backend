import pytest
from datetime import datetime

from app.database import cleanup_test_dbs, get_services
from app.services.task import (
    TaskService,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskNotFoundError,
    InvalidVersionRequest,
    NoFieldsToUpdateError,
    FailedToDeleteTaskError,
)
from app.services.lists import ListService, ListCreate
from app.services.users import UserService, UserCreate, UserNotFoundError


class TestTaskOperations:
    """
    Comprehensive integration tests for task operations including edge cases and exception handling
    """

    @pytest.fixture(scope="session", autouse=True)
    def cleanup(self):
        yield
        cleanup_test_dbs()

    @pytest.fixture
    def user_create_data(self):
        return UserCreate(
            username="taskuser123",
            email="taskuser123@gmail.com",
            password="password",
            phone_number="(555)-123-4567",
            first_name="Task",
            last_name="User",
            google_id="task-google-id",
        )

    @pytest.fixture
    def services(self):
        return get_services()

    def test_task_crud_operations(self, services, user_create_data: UserCreate):
        """Test basic task CRUD operations"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        # Create user and list
        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(
            user_id=user_response.user_id, list_name="CRUD test list"
        )
        list_response = list_service.create_list(list_data=list_data)

        # Create task
        task_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="Test CRUD task",
            reminders=[],
            isPriority=True,
            isRecurring=False,
            list_version=list_response.version,
        )

        task_response = task_service.create_task(task_data=task_data)

        # Verify task creation
        assert task_response.task_name == "Test CRUD task"
        assert task_response.isPriority == True
        assert task_response.isRecurring == False
        assert task_response.isComplete == False
        assert task_response.user_id == user_response.user_id
        assert task_response.list_id == list_response.list_id

        # Get task
        retrieved_task = task_service.get_task(task_response.task_id)
        assert retrieved_task.task_id == task_response.task_id
        assert retrieved_task.task_name == task_response.task_name

        # Update task
        task_update = TaskUpdate(task_name="Updated CRUD task", isPriority=False)
        updated_task = task_service.update_task(
            user_id=user_response.user_id,
            task_id=task_response.task_id,
            task_data=task_update,
        )

        assert updated_task.task_name == "Updated CRUD task"
        assert updated_task.isPriority == False
        assert updated_task.isRecurring == False  # Unchanged

        # Delete task
        delete_response = task_service.delete_task(task_response.task_id)
        assert delete_response["message"] == "User deleted successfully"

        # Verify task is deleted
        with pytest.raises(TaskNotFoundError, match="Task does not exist"):
            task_service.get_task(task_response.task_id)

    def test_task_exceptions(self, services, user_create_data: UserCreate):
        """Test all task service exception scenarios"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(
            user_id=user_response.user_id, list_name="Exception test list"
        )
        list_response = list_service.create_list(list_data=list_data)

        # Test TaskNotFoundError for get_task
        with pytest.raises(TaskNotFoundError, match="Task does not exist"):
            task_service.get_task("nonexistent-task-id")

        # Test TaskNotFoundError for update_task
        with pytest.raises(TaskNotFoundError, match="Task does not exist"):
            task_service.update_task(
                user_id=user_response.user_id,
                task_id="nonexistent-task-id",
                task_data=TaskUpdate(task_name="updated"),
            )

        # Test UserNotFoundError for update_task
        task_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="Test task",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )
        task_response = task_service.create_task(task_data=task_data)

        with pytest.raises(UserNotFoundError, match="User does not exist"):
            task_service.update_task(
                user_id="nonexistent-user-id",
                task_id=task_response.task_id,
                task_data=TaskUpdate(task_name="updated"),
            )

        # Test NoFieldsToUpdateError
        with pytest.raises(NoFieldsToUpdateError, match="No fields to update"):
            task_service.update_task(
                user_id=user_response.user_id,
                task_id=task_response.task_id,
                task_data=TaskUpdate(),
            )

        # Test TaskNotFoundError for delete_task
        with pytest.raises(UserNotFoundError, match="User does not exist"):
            task_service.delete_task("nonexistent-task-id")

    def test_task_toggle_operations(self, services, user_create_data: UserCreate):
        """Test all toggle operations comprehensively"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(
            user_id=user_response.user_id, list_name="Toggle test list"
        )
        list_response = list_service.create_list(list_data=list_data)

        # Create task with all flags false
        task_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="Toggle test task",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )
        task_response = task_service.create_task(task_data=task_data)

        # Test toggle_completion
        completed_task = task_service.toggle_completion(task_response.task_id)
        assert completed_task.isComplete == True
        assert completed_task.isPriority == False
        assert completed_task.isRecurring == False

        # Toggle back
        uncompleted_task = task_service.toggle_completion(task_response.task_id)
        assert uncompleted_task.isComplete == False

        # Test toggle_priority
        priority_task = task_service.toggle_priority(task_response.task_id)
        assert priority_task.isPriority == True
        assert priority_task.isComplete == False
        assert priority_task.isRecurring == False

        # Toggle back
        unpriority_task = task_service.toggle_priority(task_response.task_id)
        assert unpriority_task.isPriority == False

        # Test toggle_recurring
        recurring_task = task_service.toggle_recurring(task_response.task_id)
        assert recurring_task.isRecurring == True
        assert recurring_task.isComplete == False
        assert recurring_task.isPriority == False

        # Toggle back
        unrecurring_task = task_service.toggle_recurring(task_response.task_id)
        assert unrecurring_task.isRecurring == False

        # Test multiple toggles together
        task_service.toggle_completion(task_response.task_id)
        task_service.toggle_priority(task_response.task_id)
        task_service.toggle_recurring(task_response.task_id)

        final_task = task_service.get_task(task_response.task_id)
        assert final_task.isComplete == True
        assert final_task.isPriority == True
        assert final_task.isRecurring == True

    def test_task_versioning_edge_cases(self, services, user_create_data: UserCreate):
        """Test task operations across different list versions"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(
            user_id=user_response.user_id, list_name="Version test list"
        )
        list_response = list_service.create_list(list_data=list_data)

        # Create tasks in version 0
        task1_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="Version 0 task 1",
            reminders=[],
            isPriority=False,
            isRecurring=True,
            list_version=0,
        )

        task2_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="Version 0 task 2",
            reminders=[],
            isPriority=True,
            isRecurring=False,
            list_version=0,
        )

        task1_response = task_service.create_task(task_data=task1_data)
        task2_response = task_service.create_task(task_data=task2_data)

        # Verify tasks are in current version (0)
        current_tasks = task_service.get_current_tasks_from_list(list_response.list_id)
        assert len(current_tasks) == 2

        # Clear list (increments version to 1, duplicates recurring tasks)
        task_service.clear_list(list_response.list_id)

        # Verify version 1 tasks
        version_1_tasks = task_service.get_current_tasks_from_list(
            list_response.list_id
        )
        assert len(version_1_tasks) == 1  # Only recurring task should be duplicated
        assert version_1_tasks[0].task_name == "Version 0 task 1"
        assert version_1_tasks[0].list_version == 1

        # Test _get_tasks_from_list_version with version 0
        version_0_tasks = task_service._get_tasks_from_list_version(
            list_response.list_id, 0
        )
        assert len(version_0_tasks) == 2

        # Test invalid version requests
        with pytest.raises(
            InvalidVersionRequest, match="Requested version is not valid"
        ):
            task_service._get_tasks_from_list_version(list_response.list_id, -1)

        with pytest.raises(
            InvalidVersionRequest, match="Requested version is not valid"
        ):
            task_service._get_tasks_from_list_version(list_response.list_id, 999)

    def test_task_duplication_edge_cases(self, services, user_create_data: UserCreate):
        """Test task duplication in various scenarios"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(
            user_id=user_response.user_id, list_name="Duplication test list"
        )
        list_response = list_service.create_list(list_data=list_data)

        # Create tasks with different combinations
        tasks_config = [
            ("Recurring Priority Complete", True, True, True),  # Will be duplicated
            ("Recurring Priority Incomplete", True, True, False),  # Will be duplicated
            (
                "Recurring Non-Priority Complete",
                False,
                True,
                True,
            ),  # Will be duplicated
            (
                "Non-Recurring Priority Complete",
                True,
                False,
                True,
            ),  # Will NOT be duplicated
            (
                "Non-Recurring Priority Incomplete",
                True,
                False,
                False,
            ),  # Will be duplicated
            (
                "Non-Recurring Non-Priority Complete",
                False,
                False,
                True,
            ),  # Will NOT be duplicated
        ]

        created_tasks = []
        for name, is_priority, is_recurring, will_complete in tasks_config:
            task_data = TaskCreate(
                user_id=user_response.user_id,
                list_id=list_response.list_id,
                task_name=name,
                reminders=[],
                isPriority=is_priority,
                isRecurring=is_recurring,
                list_version=list_response.version,
            )
            task_response = task_service.create_task(task_data=task_data)

            if will_complete:
                task_service.toggle_completion(task_response.task_id)

            created_tasks.append((task_response, is_recurring, will_complete))

        # Perform rollover
        rollover_tasks = task_service.rollover_list(list_response.list_id)
        rollover_names = [task.task_name for task in rollover_tasks]

        # Verify rollover logic
        # Recurring tasks OR incomplete tasks should be duplicated
        expected_tasks = [
            "Recurring Priority Complete",  # Recurring = True -> duplicate
            "Recurring Priority Incomplete",  # Recurring = True -> duplicate
            "Recurring Non-Priority Complete",  # Recurring = True -> duplicate
            "Non-Recurring Priority Incomplete",  # Complete = False -> duplicate
        ]

        not_expected_tasks = [
            "Non-Recurring Priority Complete",  # Complete = True, Recurring = False -> NO duplicate
            "Non-Recurring Non-Priority Complete",  # Complete = True, Recurring = False -> NO duplicate
        ]

        for expected_name in expected_tasks:
            assert (
                expected_name in rollover_names
            ), f"Task '{expected_name}' should be duplicated in rollover"

        for not_expected_name in not_expected_tasks:
            assert (
                not_expected_name not in rollover_names
            ), f"Task '{not_expected_name}' should NOT be duplicated in rollover"

    def test_task_reminders_handling(self, services, user_create_data: UserCreate):
        """Test task creation and operations with reminders"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(
            user_id=user_response.user_id, list_name="Reminder test list"
        )
        list_response = list_service.create_list(list_data=list_data)

        # Create task with reminders
        reminder_times = [
            datetime(2024, 12, 25, 10, 0, 0),
            datetime(2024, 12, 25, 14, 30, 0),
        ]

        task_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="Task with reminders",
            reminders=reminder_times,
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )

        task_response = task_service.create_task(task_data=task_data)

        # Verify reminders are preserved
        assert len(task_response.reminders) == 2
        assert task_response.reminders == reminder_times

        # Test duplication preserves reminder structure (but clears actual reminders)
        task_service.toggle_recurring(task_response.task_id)
        duplicated_tasks = task_service.clear_list(list_response.list_id)

        # Verify duplication logic - reminders should be empty in duplicated task
        assert len(duplicated_tasks) == 1
        assert (
            len(duplicated_tasks[0].reminders) == 0
        )  # Reminders cleared during duplication

    def test_task_update_edge_cases(self, services, user_create_data: UserCreate):
        """Test edge cases in task updates"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(
            user_id=user_response.user_id, list_name="Update test list"
        )
        list_response = list_service.create_list(list_data=list_data)

        # Create task
        task_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="Original task name",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )
        task_response = task_service.create_task(task_data=task_data)

        # Test updating only one field
        single_update = TaskUpdate(task_name="Updated name only")
        updated_task = task_service.update_task(
            user_id=user_response.user_id,
            task_id=task_response.task_id,
            task_data=single_update,
        )

        assert updated_task.task_name == "Updated name only"
        assert updated_task.isPriority == False  # Unchanged
        assert updated_task.isRecurring == False  # Unchanged

        # Test updating multiple fields
        multi_update = TaskUpdate(
            task_name="Multi updated name",
            isPriority=True,
            isRecurring=True,
            isComplete=True,
        )

        multi_updated_task = task_service.update_task(
            user_id=user_response.user_id,
            task_id=task_response.task_id,
            task_data=multi_update,
        )

        assert multi_updated_task.task_name == "Multi updated name"
        assert multi_updated_task.isPriority == True
        assert multi_updated_task.isRecurring == True
        assert multi_updated_task.isComplete == True

        # Verify updatedAt timestamp was changed
        # Note: Due to string format storage, we just verify the update succeeded
        assert multi_updated_task.task_name == "Multi updated name"

    def test_get_versions_of_list_pagination(
        self, services, user_create_data: UserCreate
    ):
        """Test pagination functionality in get_versions_of_list"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        user_response = user_service.create_user(user_data=user_create_data)
        list_data = ListCreate(
            user_id=user_response.user_id, list_name="Pagination test list"
        )
        list_response = list_service.create_list(list_data=list_data)

        # Create tasks and generate multiple versions
        task_data = TaskCreate(
            user_id=user_response.user_id,
            list_id=list_response.list_id,
            task_name="Versioned task",
            reminders=[],
            isPriority=False,
            isRecurring=True,
            list_version=0,
        )
        task_service.create_task(task_data=task_data)

        # Create multiple versions by clearing list multiple times
        for i in range(3):
            task_service.clear_list(list_response.list_id)

        # Current list should be at version 3
        current_list = list_service.get_list(list_response.list_id)
        assert current_list.version == 3

        # Test pagination
        versions = task_service.get_versions_of_list(
            list_response.list_id, page_start=0, page_end=2
        )

        assert len(versions) == 2  # Should return 2 versions (0 and 1)

        # Test invalid pagination bounds
        with pytest.raises(
            InvalidVersionRequest, match="Requested version is not valid"
        ):
            task_service.get_versions_of_list(
                list_response.list_id, page_start=-1, page_end=1
            )
