# tests/test_services/test_task_service.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.services.task import *
from app.services.lists import ListNotFoundError
from app.services.users import UserNotFoundError

class TestTaskService:
    """
    Unit tests for TaskService
    
    Mock Explanation:
    - Mock objects are fake objects that simulate real objects
    - They let us test our code without using a real database
    - We can control what they return and verify they were called correctly
    """

    @pytest.fixture
    def mock_task_collection(self):
        """Create a mock MongoDB collection for tasks"""
        return Mock()

    @pytest.fixture
    def mock_user_service(self):
        """Create a mock UserService"""
        return Mock()
    
    @pytest.fixture
    def mock_list_service(self):
        """Create a mock ListService"""
        return Mock()
    
    @pytest.fixture
    def task_service(self, mock_task_collection, mock_user_service, mock_list_service):
        """
        Create TaskService with mocked dependencies
        
        Dependency Injection Process:
        1. Create TaskService with fake database collection
        2. Replace real UserService with mock
        3. Replace real ListService with mock
        """
        service = TaskService(task_collection=mock_task_collection)
        service.user_service = mock_user_service
        service.list_service = mock_list_service
        
        return service
    
    @pytest.fixture
    def sample_task_create(self):
        """Sample data for creating a Task"""
        return TaskCreate(
            user_id="user-123",
            list_id="list-123",
            task_name="clean room",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=0,
        )
    
    @pytest.fixture
    def sample_task_doc(self):
        """Sample task document as stored in database"""
        return {
            "user_id": "user-123",
            "list_id": "list-123",
            "task_id": "task-456",
            "task_name": "clean room",
            "reminders": [],
            "isComplete": False,
            "isPriority": False,
            "isRecurring": False,
            "createdAt": datetime(2024, 1, 1, 12, 0, 0),
            "updatedAt": datetime(2024, 1, 1, 12, 0, 0),
            "list_version": 0
        }
    
    @pytest.fixture
    def sample_recurring_task_doc(self):
        """Sample recurring task document"""
        return {
            "user_id": "user-123",
            "list_id": "list-123",
            "task_id": "task-789",
            "task_name": "take trash out",
            "reminders": [],
            "isComplete": False,
            "isPriority": False,
            "isRecurring": True,
            "createdAt": datetime(2024, 1, 1, 12, 0, 0),
            "updatedAt": datetime(2024, 1, 1, 12, 0, 0),
            "list_version": 0
        }

    # CRUD Tests:
    
    def test_create_task_success(self, task_service, mock_task_collection, 
                               mock_user_service, mock_list_service, sample_task_create):
        """
        Test successful task creation
        
        Mock Flow:
        1. Tell mock_user_service.user_exists() to return True
        2. Tell mock_list_service.list_exists() to return True  
        3. Call task_service.create_task()
        4. Verify mock_task_collection.insert_one() was called
        """
        # Step 1: Set up mock responses
        mock_user_service.user_exists.return_value = True
        mock_list_service.list_exists.return_value = True
        
        # Step 2: Call the method we're testing
        result = task_service.create_task(sample_task_create)
        
        # Step 3: Verify mocks were called correctly
        mock_user_service.user_exists.assert_called_once_with("user-123")
        mock_list_service.list_exists.assert_called_once_with("list-123")
        mock_task_collection.insert_one.assert_called_once()
        
        # Step 4: Verify the result
        assert result.user_id == "user-123"
        assert result.task_name == "clean room"
        assert result.isComplete == False
    
    def test_create_task_user_not_found(self, task_service, mock_user_service, 
                                      mock_list_service, sample_task_create):
        """
        Test task creation when user doesn't exist
        
        Mock Flow:
        1. Tell mock_user_service.user_exists() to return False
        2. Call task_service.create_task()
        3. Expect UserNotFoundError to be raised
        """
        # Step 1: Mock user doesn't exist
        mock_user_service.user_exists.return_value = False
        
        # Step 2: Verify exception is raised
        with pytest.raises(UserNotFoundError, match="User does not exist"):
            task_service.create_task(sample_task_create)
    
    def test_create_task_list_not_found(self, task_service, mock_user_service, 
                                      mock_list_service, sample_task_create):
        """
        Test task creation when list doesn't exist
        """
        # User exists but list doesn't
        mock_user_service.user_exists.return_value = True
        mock_list_service.list_exists.return_value = False
        
        with pytest.raises(ListNotFoundError, match="List does not exist"):
            task_service.create_task(sample_task_create)

    def test_get_task_success(self, task_service, mock_task_collection, sample_task_doc):
        """
        Test successful task retrieval
        
        Mock Flow:
        1. Tell mock_task_collection.find_one() to return sample data
        2. Call task_service.get_task()
        3. Verify correct data is returned
        """
        # Step 1: Mock database response
        mock_task_collection.find_one.return_value = sample_task_doc
        
        # Step 2: Call method
        result = task_service.get_task("task-456")
        
        # Step 3: Verify database was queried correctly
        mock_task_collection.find_one.assert_called_once_with({"task_id": "task-456"})
        
        # Step 4: Verify result
        assert result.task_id == "task-456"
        assert result.task_name == "clean room"

    def test_get_task_not_found(self, task_service, mock_task_collection):
        """
        Test task retrieval when task doesn't exist
        """
        # Mock returns None (no task found)
        mock_task_collection.find_one.return_value = None
        
        with pytest.raises(TaskNotFoundError, match="Task does not exist"):
            task_service.get_task("nonexistent-task")

    def test_update_task_success(self, task_service, mock_task_collection, 
                               mock_user_service, sample_task_doc):
        """
        Test successful task update
        
        Mock Flow:
        1. Mock user exists
        2. Mock task exists  
        3. Mock get_task to return updated task
        4. Call update_task
        5. Verify database update was called
        """
        # Setup mocks
        mock_user_service.user_exists.return_value = True
        mock_task_collection.find_one.return_value = sample_task_doc
        
        # Mock get_task call (called at end of update_task)
        with patch.object(task_service, 'get_task') as mock_get_task:
            mock_get_task.return_value = TaskResponse(**sample_task_doc)
            
            # Create update data
            update_data = TaskUpdate(task_name="updated task name")
            
            # Call update
            result = task_service.update_task("user-123", "task-456", update_data)
            
            # Verify database update was called
            mock_task_collection.update_one.assert_called_once()
            
            # Verify get_task was called to return updated task
            mock_get_task.assert_called_once_with("task-456")

    def test_delete_task_success(self, task_service, mock_task_collection, sample_task_doc):
        """
        Test successful task deletion
        """
        # Mock task exists
        mock_task_collection.find_one.return_value = sample_task_doc
        
        # Mock successful deletion
        mock_delete_result = Mock()
        mock_delete_result.deleted_count = 1
        mock_task_collection.delete_one.return_value = mock_delete_result
        
        # Call delete
        result = task_service.delete_task("task-456")
        
        # Verify deletion was called
        mock_task_collection.delete_one.assert_called_once_with({"task_id": "task-456"})
        
        # Verify success message
        assert result["message"] == "User deleted successfully"

    # Task Functionality Tests:
    
    def test_toggle_completion_success(self, task_service, sample_task_doc):
        """
        Test toggling task completion status
        
        Mock Flow:
        1. Mock get_task to return task with isComplete=False
        2. Mock update_task to succeed
        3. Call toggle_completion
        4. Verify task completion was toggled
        """
        with patch.object(task_service, 'get_task') as mock_get_task, \
             patch.object(task_service, 'update_task') as mock_update_task:
            
            # Mock get_task returns task with isComplete=False
            mock_get_task.return_value = sample_task_doc
            
            # Call toggle
            result = task_service.toggle_completion("task-456")
            
            # Verify get_task was called
            mock_get_task.assert_called_once_with("task-456")
            
            # Verify update_task was called with toggled completion
            mock_update_task.assert_called_once()
            
            # Get the update data that was passed
            call_args = mock_update_task.call_args[0]  # Get positional args
            update_data = call_args[2]  # Third argument is the TaskUpdate object
            
            # Verify completion was toggled (False -> True)
            assert update_data.isComplete == True
            
            # Verify success message
            assert result["message"] == "Task toggle was successful"

    def test_get_current_tasks_from_list(self, task_service, mock_task_collection, 
                                       mock_list_service, sample_task_doc):
        """
        Test retrieving all current tasks from a list
        
        Mock Flow:
        1. Mock list exists
        2. Mock list service returns list with version
        3. Mock database returns list of tasks
        4. Verify correct query was made
        """
        # Mock list exists and has version 2
        mock_list_service.list_exists.return_value = True
        mock_list_service.get_list.return_value = {"version": 2}
        
        # Mock database returns list of tasks
        mock_task_collection.find.return_value = [sample_task_doc]
        
        # Call method
        result = task_service.get_current_tasks_from_list("list-123")
        
        # Verify list service was called
        mock_list_service.list_exists.assert_called_once_with("list-123")
        mock_list_service.get_list.assert_called_once_with("list-123")
        
        # Verify database query was correct
        mock_task_collection.find.assert_called_once_with({
            "list_id": "list-123", 
            "list_version": 2
        })
        
        # Verify result
        assert len(result) == 1
        assert result[0].task_id == "task-456"

    def test_clear_list_with_recurring_tasks_strategy4(self, task_service, mock_list_service, 
                                                     sample_recurring_task_doc, mock_task_collection):
        """
        Strategy 4: Hybrid approach
        - Mock get_current_tasks_from_list (avoids redundant database calls)
        - Let _duplicate_task, get_task, and create_task run with real logic
        - Mock only the database operations they need
        
        Flow being tested:
        1. clear_list calls get_current_tasks_from_list (MOCKED)
        2. clear_list calls list_service.increment_version 
        3. For recurring tasks: clear_list calls _duplicate_task (REAL)
        4. _duplicate_task calls get_task (REAL) -> task_collection.find_one (MOCKED)
        5. _duplicate_task calls create_task (REAL) -> task_collection.insert_one (MOCKED)
        6. clear_list calls get_current_tasks_from_list again (MOCKED)
        """
        with patch.object(task_service, 'get_current_tasks_from_list') as mock_get_tasks:
            
            # Create test data
            recurring_task = TaskResponse(**sample_recurring_task_doc)
            
            # Create what the new task should look like after duplication
            new_task_data = sample_recurring_task_doc.copy()
            new_task_data['task_id'] = 'new-task-id'
            new_task_data['list_version'] = 1
            new_task = TaskResponse(**new_task_data)
            
            # Mock the two calls to get_current_tasks_from_list
            mock_get_tasks.side_effect = [
                [recurring_task],  # First call: current tasks before clearing
                [new_task]         # Second call: tasks after clearing (new version)
            ]
            
            # Mock database operations for get_task (called by _duplicate_task)
            # get_task calls task_collection.find_one
            recurring_task_dict = recurring_task.model_dump()
            mock_task_collection.find_one.return_value = recurring_task_dict
            
            # Mock database operations for create_task (called by _duplicate_task)  
            # create_task calls task_collection.insert_one
            mock_task_collection.insert_one.return_value = None
            
            # Mock dependencies for create_task validation
            task_service.user_service.user_exists.return_value = True
            task_service.list_service.list_exists.return_value = True
            
            # Mock list service increment_version
            mock_list_service.increment_version.return_value = {"version": 1}
            
            # Call the method we're testing
            result = task_service.clear_list("list-123")
            
            # Verify the orchestration worked correctly
            assert mock_get_tasks.call_count == 2, "Should call get_current_tasks_from_list twice"
            
            # Verify list version was incremented
            mock_list_service.increment_version.assert_called_once_with("list-123")
            
            # Verify _duplicate_task called get_task with correct task_id
            mock_task_collection.find_one.assert_called_once_with({"task_id": "task-789"})
            
            # Verify _duplicate_task called create_task which inserted new task
            mock_task_collection.insert_one.assert_called_once()
            
            # Verify the result
            assert len(result) == 1
            assert result[0].task_id == 'new-task-id'
            assert result[0].list_version == 1
            assert result[0].isRecurring == True

    def test_rollover_list_strategy4(self, task_service, mock_list_service, 
                                    sample_recurring_task_doc, mock_task_collection):
        """
        Strategy 4: Test rollover_list (keeps incomplete and recurring tasks)
        - Mock get_current_tasks_from_list 
        - Let _duplicate_task logic run for integration testing
        - Mock only database operations
        """
        with patch.object(task_service, 'get_current_tasks_from_list') as mock_get_tasks:
            
            # Create test tasks
            recurring_task_data = sample_recurring_task_doc.copy()
            recurring_task = TaskResponse(**recurring_task_data)
            
            incomplete_task_data = sample_recurring_task_doc.copy()
            incomplete_task_data['task_id'] = 'incomplete-task-id'
            incomplete_task_data['task_name'] = 'incomplete task'
            incomplete_task_data['isRecurring'] = False
            incomplete_task_data['isComplete'] = False
            incomplete_task = TaskResponse(**incomplete_task_data)
            
            complete_task_data = sample_recurring_task_doc.copy()
            complete_task_data['task_id'] = 'complete-task-id'
            complete_task_data['task_name'] = 'complete task'
            complete_task_data['isRecurring'] = False
            complete_task_data['isComplete'] = True
            complete_task = TaskResponse(**complete_task_data)
            
            # Create expected new tasks after rollover
            new_recurring_data = recurring_task_data.copy()
            new_recurring_data['task_id'] = 'new-recurring-id'
            new_recurring_data['list_version'] = 1
            new_recurring_task = TaskResponse(**new_recurring_data)
            
            new_incomplete_data = incomplete_task_data.copy()
            new_incomplete_data['task_id'] = 'new-incomplete-id'
            new_incomplete_data['list_version'] = 1
            new_incomplete_task = TaskResponse(**new_incomplete_data)
            
            # Mock get_current_tasks_from_list calls
            mock_get_tasks.side_effect = [
                [recurring_task, incomplete_task, complete_task],  # Before rollover
                [new_recurring_task, new_incomplete_task]          # After rollover
            ]
            
            # Mock database operations for get_task calls in _duplicate_task
            mock_task_collection.find_one.side_effect = [
                recurring_task.model_dump(),   # First _duplicate_task call
                incomplete_task.model_dump()   # Second _duplicate_task call
            ]
            
            # Mock database operations for create_task calls in _duplicate_task
            mock_task_collection.insert_one.return_value = None
            
            # Mock dependencies
            task_service.user_service.user_exists.return_value = True
            task_service.list_service.list_exists.return_value = True
            mock_list_service.increment_version.return_value = {"version": 1}
            
            # Call rollover_list
            result = task_service.rollover_list("list-123")
            
            # Verify orchestration
            assert mock_get_tasks.call_count == 2
            mock_list_service.increment_version.assert_called_once_with("list-123")
            
            # Should duplicate recurring task and incomplete task, but not complete task
            assert mock_task_collection.find_one.call_count == 2
            assert mock_task_collection.insert_one.call_count == 2
            
            # Verify result contains only carried-over tasks
            assert len(result) == 2
            task_ids = [task.task_id for task in result]
            assert 'new-recurring-id' in task_ids
            assert 'new-incomplete-id' in task_ids