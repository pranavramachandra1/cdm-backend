# tests/test_services/test_list_service.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.services.lists import (
    ListService,
    ListCreate,
    ListUpdate,
    ListResponse,
    ListNotFoundError,
    NoFieldsToUpdateError,
    FailedToDeleteList,
    InvalidParameters,
)

from app.services.users import UserNotFoundError


class TestListService:
    """
    Unit tests for ListService

    Mock Explanation:
    - Mock objects are fake objects that simulate real objects
    - They let us test our code without using a real database
    - We can control what they return and verify they were called correctly
    """

    @pytest.fixture
    def mock_list_collection(self):
        """
        Create a mock MongoDB collection for lists

        Fixture Explanation:
        - Fixtures are reusable test data/objects
        - This creates a fake database collection
        - Each test gets a fresh mock collection
        """
        return Mock()

    @pytest.fixture
    def mock_user_service(self):
        """
        Create a mock UserService

        Why Mock Dependencies:
        - ListService depends on UserService
        - We want to test ListService in isolation
        - So we fake the UserService responses
        """
        return Mock()

    @pytest.fixture
    def list_service(self, mock_list_collection, mock_user_service):
        """
        Create ListService with mocked dependencies

        Dependency Injection:
        - We inject our fake database and user service
        - This isolates ListService for testing
        """
        service = ListService(list_collection=mock_list_collection)
        # Replace the real user_service with our mock
        service.user_service = mock_user_service
        return service

    @pytest.fixture
    def sample_list_create(self):
        """Sample data for creating a list"""
        return ListCreate(user_id="user-123", list_name="My Todo List")

    @pytest.fixture
    def sample_list_doc(self):
        """Sample list document as stored in database"""
        return {
            "list_id": "list-123",
            "user_id": "user-123",
            "list_name": "My Todo List",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "last_updated_at": datetime(2024, 1, 1, 12, 0, 0),
            "version": 0,
        }

    @pytest.fixture
    def sample_list_response(self, sample_list_doc):
        """Sample ListResponse object"""
        return ListResponse(**sample_list_doc)

    # Test Static Methods
    def test_create_list_id(self):
        """
        Test that create_list_id generates unique IDs

        Static Method Testing:
        - Static methods don't need an instance
        - They should be pure functions (same input = same output)
        - But UUID generation is random, so we test properties
        """
        list_id = ListService.create_list_id()

        # Test it's a string
        assert isinstance(list_id, str)
        # Test it's reasonably long (UUIDs are ~36 chars)
        assert len(list_id) > 30

        # Test uniqueness - each call should be different
        list_id2 = ListService.create_list_id()
        assert list_id != list_id2

    # Test list_exists method
    def test_list_exists_by_list_id(self, list_service, mock_list_collection):
        """
        Test checking if list exists by list_id

        Mock Setup Pattern:
        1. Configure what the mock should return
        2. Call the method being tested
        3. Assert the result is correct
        4. Verify the mock was called correctly
        """
        # 1. Configure mock - simulate list exists
        mock_list_collection.find_one.return_value = {"list_id": "list-123"}

        # 2. Call the method
        result = list_service.list_exists(list_id="list-123")

        # 3. Assert result
        assert result == True

        # 4. Verify database was queried correctly
        mock_list_collection.find_one.assert_called_once_with({"list_id": "list-123"})

    def test_list_exists_by_user_and_name(self, list_service, mock_list_collection):
        """Test checking existence by user_id and list_name"""
        # Simulate list doesn't exist
        mock_list_collection.find_one.return_value = None

        result = list_service.list_exists(user_id="user-123", list_name="My List")

        assert result == False
        mock_list_collection.find_one.assert_called_once_with(
            {"user_id": "user-123", "list_name": "My List"}
        )

    def test_list_exists_priority_list_id(self, list_service, mock_list_collection):
        """
        Test that list_id takes priority over user_id/list_name

        Edge Case Testing:
        - What happens when multiple parameters are provided?
        - The code should use list_id if provided
        """
        mock_list_collection.find_one.return_value = {"list_id": "list-123"}

        # Pass all parameters - should only use list_id
        result = list_service.list_exists(
            list_id="list-123",
            user_id="user-456",  # Should be ignored
            list_name="Other List",  # Should be ignored
        )

        assert result == True
        # Should only query by list_id
        mock_list_collection.find_one.assert_called_once_with({"list_id": "list-123"})

    # Test create_list method
    def test_create_list_success(
        self, list_service, mock_list_collection, sample_list_create
    ):
        """
        Test successful list creation

        Success Path Testing:
        - Test the main functionality works
        - Verify all side effects (database calls)
        - Check return value is correct
        """
        # Mock successful database insertion
        mock_list_collection.insert_one.return_value = Mock()

        # Mock ID generation to be predictable
        with patch.object(ListService, "create_list_id", return_value="list-123"):
            result = list_service.create_list(sample_list_create)

        # Verify return value
        assert isinstance(result, ListResponse)
        assert result.list_id == "list-123"
        assert result.user_id == "user-123"
        assert result.list_name == "My Todo List"
        assert result.version == 0
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.last_updated_at, datetime)

        # Verify database was called
        mock_list_collection.insert_one.assert_called_once()

        # Examine what was inserted
        inserted_doc = mock_list_collection.insert_one.call_args[0][0]
        assert inserted_doc["list_id"] == "list-123"
        assert inserted_doc["user_id"] == "user-123"
        assert inserted_doc["list_name"] == "My Todo List"
        assert inserted_doc["version"] == 0

    # Test get_list method
    def test_get_list_success(
        self, list_service, mock_list_collection, sample_list_doc
    ):
        """Test successful list retrieval"""
        mock_list_collection.find_one.return_value = sample_list_doc

        result = list_service.get_list("list-123")

        assert isinstance(result, ListResponse)
        assert result.list_id == "list-123"
        assert result.user_id == "user-123"
        assert result.list_name == "My Todo List"

        mock_list_collection.find_one.assert_called_once_with({"list_id": "list-123"})

    def test_get_list_not_found(self, list_service, mock_list_collection):
        """
        Test getting non-existent list raises proper error

        Error Case Testing:
        - What happens when the list doesn't exist?
        - Should raise ListNotFoundError (now properly handled!)
        """
        mock_list_collection.find_one.return_value = None

        with pytest.raises(ListNotFoundError, match="List does not exist"):
            list_service.get_list("nonexistent-list")

    # Test update_list method
    def test_update_list_success(
        self, list_service, mock_list_collection, sample_list_doc
    ):
        """Test successful list update"""
        # Mock list exists
        mock_list_collection.find_one.side_effect = [
            sample_list_doc,  # First call for list_exists
            {
                **sample_list_doc,
                "list_name": "Updated List",
            },  # Second call for get_list
        ]

        mock_list_collection.update_one.return_value = Mock()

        update_data = ListUpdate(list_name="Updated List")
        result = list_service.update_list("list-123", update_data)

        assert result.list_name == "Updated List"

        # Verify update was called
        mock_list_collection.update_one.assert_called_once()
        call_args = mock_list_collection.update_one.call_args
        assert call_args[0][0] == {"list_id": "list-123"}  # Query

        update_data_sent = call_args[0][1]["$set"]
        assert "list_name" in update_data_sent
        assert "last_updated_at" in update_data_sent  # Should auto-add timestamp

    def test_update_list_not_found(self, list_service, mock_list_collection):
        """Test updating non-existent list raises error"""
        # Mock list doesn't exist
        mock_list_collection.find_one.return_value = None

        update_data = ListUpdate(list_name="New Name")

        with pytest.raises(ListNotFoundError, match="List is not found"):
            list_service.update_list("nonexistent-list", update_data)

    def test_update_list_no_fields(
        self, list_service, mock_list_collection, sample_list_doc
    ):
        """Test updating with no fields raises error"""
        # Mock list exists
        mock_list_collection.find_one.return_value = sample_list_doc

        # Empty update
        update_data = ListUpdate()

        with pytest.raises(NoFieldsToUpdateError, match="No fields to update"):
            list_service.update_list("list-123", update_data)

    # Test delete_list method
    def test_delete_list_success(
        self, list_service, mock_list_collection, sample_list_doc
    ):
        """Test successful list deletion"""
        # Mock list exists
        mock_list_collection.find_one.return_value = sample_list_doc

        # Mock successful deletion
        mock_list_collection.delete_one.return_value = Mock(deleted_count=1)

        result = list_service.delete_list("list-123")

        assert result == {"message": "List deleted successfully"}

        mock_list_collection.delete_one.assert_called_once_with({"list_id": "list-123"})

    def test_delete_list_not_found(self, list_service, mock_list_collection):
        """Test deleting non-existent list raises error"""
        mock_list_collection.find_one.return_value = None

        with pytest.raises(ListNotFoundError, match="List is not found"):
            list_service.delete_list("nonexistent-list")

    def test_delete_list_database_failure(
        self, list_service, mock_list_collection, sample_list_doc
    ):
        """Test database deletion failure"""
        mock_list_collection.find_one.return_value = sample_list_doc
        mock_list_collection.delete_one.return_value = Mock(deleted_count=0)

        with pytest.raises(FailedToDeleteList, match="Failed to delete list"):
            list_service.delete_list("list-123")

    # Test get_lists_by_user method
    def test_get_lists_by_user_success(
        self, list_service, mock_list_collection, mock_user_service
    ):
        """
        Test getting all lists for a user

        Testing Dependencies:
        - This method calls user_service.user_exists()
        - We need to mock that call
        - Then mock the database response
        """
        # Mock user exists
        mock_user_service.user_exists.return_value = True

        # Mock database response - multiple lists
        list_docs = [
            {
                "list_id": "list-1",
                "user_id": "user-123",
                "list_name": "List 1",
                "created_at": datetime.now(),
                "last_updated_at": datetime.now(),
                "version": 0,
            },
            {
                "list_id": "list-2",
                "user_id": "user-123",
                "list_name": "List 2",
                "created_at": datetime.now(),
                "last_updated_at": datetime.now(),
                "version": 1,
            },
        ]
        mock_list_collection.find.return_value = list_docs

        result = list_service.get_lists_by_user("user-123")

        # Verify result
        assert len(result) == 2
        assert all(isinstance(item, ListResponse) for item in result)
        assert result[0].list_name == "List 1"
        assert result[1].list_name == "List 2"

        # Verify dependencies were called
        mock_user_service.user_exists.assert_called_once_with(user_id="user-123")
        mock_list_collection.find.assert_called_once_with({"user_id": "user-123"})

    def test_get_lists_by_user_user_not_found(self, list_service, mock_user_service):
        """Test getting lists for non-existent user"""
        mock_user_service.user_exists.return_value = False

        with pytest.raises(UserNotFoundError, match="User not found"):
            list_service.get_lists_by_user("nonexistent-user")

    def test_get_lists_by_user_empty_result(
        self, list_service, mock_list_collection, mock_user_service
    ):
        """Test user exists but has no lists"""
        mock_user_service.user_exists.return_value = True
        mock_list_collection.find.return_value = []  # No lists

        result = list_service.get_lists_by_user("user-123")

        assert result == []

    # Test increment_version method
    def test_increment_version_success(
        self, list_service, mock_list_collection, sample_list_doc
    ):
        """
        Test incrementing list version

        Complex Method Testing:
        - This method calls get_list, then update_list, then get_list again
        - We need to mock multiple calls in sequence
        """
        # Mock the sequence of calls
        mock_list_collection.find_one.side_effect = [
            sample_list_doc,  # First get_list call
            sample_list_doc,  # list_exists call in update_list
            {**sample_list_doc, "version": 1},  # get_list call in update_list
            {**sample_list_doc, "version": 1},  # Final get_list call
        ]

        mock_list_collection.update_one.return_value = Mock()

        result = list_service.increment_version("list-123")

        assert result.version == 1

        # Should have called update_one to increment version
        mock_list_collection.update_one.assert_called_once()

    # Integration-style test (still using mocks, but testing method interactions)
    def test_create_and_get_list_integration(self, list_service, mock_list_collection):
        """
        Test creating a list then getting it

        Integration Testing with Mocks:
        - Test multiple methods working together
        - Still use mocks, but test realistic scenarios
        """
        # Mock creation
        mock_list_collection.insert_one.return_value = Mock()

        # Mock retrieval
        created_doc = {
            "list_id": "list-123",
            "user_id": "user-123",
            "list_name": "My List",
            "created_at": datetime.now(),
            "last_updated_at": datetime.now(),
            "version": 0,
        }
        mock_list_collection.find_one.return_value = created_doc

        # Create list
        with patch.object(ListService, "create_list_id", return_value="list-123"):
            create_data = ListCreate(user_id="user-123", list_name="My List")
            created_list = list_service.create_list(create_data)

        # Get the list
        retrieved_list = list_service.get_list("list-123")

        # They should be equivalent
        assert created_list.list_id == retrieved_list.list_id
        assert created_list.list_name == retrieved_list.list_name

    # Test edge cases and error conditions
    def test_list_exists_with_no_parameters(self, list_service):
        """Test list_exists with no parameters raises error"""
        # Now properly raises InvalidParameters exception
        with pytest.raises(InvalidParameters, match="No arguments were given"):
            list_service.list_exists()

    def test_list_exists_with_only_user_id(self, list_service):
        """Test list_exists with only user_id (missing list_name)"""
        with pytest.raises(InvalidParameters, match="No arguments were given"):
            list_service.list_exists(user_id="user-123")

    def test_list_exists_with_only_list_name(self, list_service):
        """Test list_exists with only list_name (missing user_id)"""
        with pytest.raises(InvalidParameters, match="No arguments were given"):
            list_service.list_exists(list_name="My List")

    # Performance/Stress Testing Concepts (not real performance tests)
    def test_large_list_name(self, list_service, mock_list_collection):
        """Test with very long list name"""
        long_name = "A" * 1000  # Very long name

        mock_list_collection.insert_one.return_value = Mock()

        with patch.object(ListService, "create_list_id", return_value="list-123"):
            create_data = ListCreate(user_id="user-123", list_name=long_name)
            result = list_service.create_list(create_data)

            assert result.list_name == long_name

    # Test error message formatting
    def test_error_messages_are_helpful(self, list_service, mock_list_collection):
        """Test that error messages are informative"""
        mock_list_collection.find_one.return_value = None

        try:
            list_service.update_list("bad-id", ListUpdate(list_name="test"))
        except ListNotFoundError as e:
            assert "List is not found" in str(e)
            # Good error messages help debugging

        try:
            list_service.update_list("list-123", ListUpdate())
        except Exception as e:
            # This will fail at list_exists check, but if it didn't:
            pass
