# tests/test_services/test_users.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.services.users import (
    UserService,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserAlreadyExistsError,
    UserNotFoundError,
    NoFieldsToUpdateError,
)


class TestUserService:
    """
    Unit tests for UserService
    """

    @pytest.fixture
    def mock_collection(self):
        """Create a mock MongoDB collection"""
        return Mock()

    @pytest.fixture
    def user_service(self, mock_collection):
        """Create UserService with mocked database"""
        return UserService(user_collection=mock_collection)

    @pytest.fixture
    def sample_user_create(self):
        """Sample user creation data"""
        return UserCreate(
            username="testuser",
            email="test@example.com",
            password="securepassword123",
            phone_number="+1234567890",
            first_name="John",
            last_name="Doe",
        )

    @pytest.fixture
    def sample_user_doc(self):
        """Sample user document as stored in database"""
        return {
            "user_id": "test-user-id-123",
            "username": "testuser",
            "email": "test@example.com",
            "password": "$2b$12$hashedpassword",  # Mock hashed password
            "phone_number": "+1234567890",
            "first_name": "John",
            "last_name": "Doe",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "last_updated_at": datetime(2024, 1, 1, 12, 0, 0),
        }

    # Test Static Methods
    def test_hash_password(self):
        """Test password hashing works"""
        password = "mypassword123"
        hashed = UserService._hash_password(password)

        assert hashed != password  # Should be different
        assert len(hashed) > 20  # Should be longer
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_verify_password(self):
        """Test password verification works"""
        password = "mypassword123"
        hashed = UserService._hash_password(password)

        # Correct password should verify
        assert UserService._verify_password(password, hashed) == True

        # Wrong password should not verify
        assert UserService._verify_password("wrongpassword", hashed) == False

    def test_create_user_id(self):
        """Test user ID generation"""
        user_id = UserService.create_user_id()

        assert isinstance(user_id, str)
        assert len(user_id) > 20  # UUID should be reasonably long

        # Each call should generate unique ID
        user_id2 = UserService.create_user_id()
        assert user_id != user_id2

    # Test user_exists method
    def test_user_exists_by_username(self, user_service, mock_collection):
        """Test checking if user exists by username"""
        # Mock database response
        mock_collection.find_one.return_value = {"username": "testuser"}

        result = user_service.user_exists(username="testuser")

        assert result == True
        mock_collection.find_one.assert_called_once_with(
            {"$or": [{"username": "testuser"}]}
        )

    def test_user_exists_by_multiple_fields(self, user_service, mock_collection):
        """Test checking existence by multiple fields"""
        mock_collection.find_one.return_value = None  # User doesn't exist

        result = user_service.user_exists(username="testuser", email="test@example.com")

        assert result == False
        mock_collection.find_one.assert_called_once_with(
            {"$or": [{"username": "testuser"}, {"email": "test@example.com"}]}
        )

    def test_user_exists_no_conditions(self, user_service):
        """Test user_exists with no parameters returns False"""
        result = user_service.user_exists()
        assert result == False

    # Test create_user method
    def test_create_user_success(
        self, user_service, mock_collection, sample_user_create
    ):
        """Test successful user creation"""
        # Mock that user doesn't exist
        mock_collection.find_one.return_value = None

        # Mock successful insertion
        mock_collection.insert_one.return_value = Mock()

        # Mock UUID generation to be predictable
        with patch.object(UserService, "create_user_id", return_value="test-id-123"):
            result = user_service.create_user(sample_user_create)

        # Verify result
        assert isinstance(result, UserResponse)
        assert result.user_id == "test-id-123"
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.first_name == "John"
        assert result.last_name == "Doe"

        # Verify database was called
        mock_collection.insert_one.assert_called_once()

        # Verify the inserted document structure
        call_args = mock_collection.insert_one.call_args[0][0]
        assert call_args["user_id"] == "test-id-123"
        assert call_args["username"] == "testuser"
        assert "password" in call_args  # Password should be included in DB
        assert call_args["password"] != "securepassword123"  # Should be hashed

    def test_create_user_already_exists(
        self, user_service, mock_collection, sample_user_create
    ):
        """Test creating user that already exists raises error"""
        # Mock that user already exists
        mock_collection.find_one.return_value = {"username": "testuser"}

        with pytest.raises(UserAlreadyExistsError, match="User already exists"):
            user_service.create_user(sample_user_create)

        # Should not call insert_one since user exists
        mock_collection.insert_one.assert_not_called()

    def test_create_user_invalid_email(self):
        """Test creating user with invalid email raises validation error"""

        # Test that Pydantic validation catches invalid email at model creation
        with pytest.raises(ValueError, match="Invalid email format"):
            UserCreate(
                username="testuser",
                email="invalid-email",  # No @ symbol
                password="password123",
                phone_number="+1234567890",
                first_name="John",
                last_name="Doe",
            )

    # Test get_user method
    def test_get_user_success(self, user_service, mock_collection, sample_user_doc):
        """Test successful user retrieval"""
        mock_collection.find_one.return_value = sample_user_doc

        result = user_service.get_user("test-user-id-123")

        assert isinstance(result, UserResponse)
        assert result.user_id == "test-user-id-123"
        assert result.username == "testuser"

        mock_collection.find_one.assert_called_once_with(
            {"user_id": "test-user-id-123"}
        )

    def test_get_user_not_found(self, user_service, mock_collection):
        """Test getting non-existent user raises error"""
        mock_collection.find_one.return_value = None

        with pytest.raises(UserNotFoundError, match="User not found"):
            user_service.get_user("nonexistent-id")

    def test_get_user_excludes_password(
        self, user_service, mock_collection, sample_user_doc
    ):
        """Test that password is not included in response"""
        mock_collection.find_one.return_value = sample_user_doc

        result = user_service.get_user("test-user-id-123")

        # Password should not be in the response
        assert not hasattr(result, "password")

    # Test update_user method
    def test_update_user_success(self, user_service, mock_collection, sample_user_doc):
        """Test successful user update"""
        # Mock user exists check
        mock_collection.find_one.side_effect = [
            sample_user_doc,  # First call for user_exists
            {**sample_user_doc, "first_name": "Jane"},  # Second call for get_user
        ]

        # Mock successful update
        mock_collection.update_one.return_value = Mock()

        update_data = UserUpdate(first_name="Jane")
        result = user_service.update_user("test-user-id-123", update_data)

        assert result.first_name == "Jane"

        # Verify update was called with correct data
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args
        assert call_args[0][0] == {"user_id": "test-user-id-123"}  # Query
        assert "first_name" in call_args[0][1]["$set"]  # Update data
        assert "last_updated_at" in call_args[0][1]["$set"]  # Timestamp added

    def test_update_user_not_found(self, user_service, mock_collection):
        """Test updating non-existent user raises error"""
        mock_collection.find_one.return_value = None  # User doesn't exist

        update_data = UserUpdate(first_name="Jane")

        with pytest.raises(UserNotFoundError, match="User not found"):
            user_service.update_user("nonexistent-id", update_data)

    def test_update_user_no_fields(
        self, user_service, mock_collection, sample_user_doc
    ):
        """Test updating with no fields raises error"""
        mock_collection.find_one.return_value = sample_user_doc

        # Empty update (no fields set)
        update_data = UserUpdate()

        with pytest.raises(NoFieldsToUpdateError, match="No fields to update"):
            user_service.update_user("test-user-id-123", update_data)

    # Test delete_user method
    def test_delete_user_success(self, user_service, mock_collection, sample_user_doc):
        """Test successful user deletion"""
        mock_collection.find_one.return_value = sample_user_doc
        mock_collection.delete_one.return_value = Mock(deleted_count=1)

        result = user_service.delete_user("test-user-id-123")

        assert result == {"message": "User deleted successfully"}
        mock_collection.delete_one.assert_called_once_with(
            {"user_id": "test-user-id-123"}
        )

    def test_delete_user_not_found(self, user_service, mock_collection):
        """Test deleting non-existent user raises error"""
        mock_collection.find_one.return_value = None

        with pytest.raises(UserNotFoundError, match="User not found"):
            user_service.delete_user("nonexistent-id")

    def test_delete_user_database_failure(
        self, user_service, mock_collection, sample_user_doc
    ):
        """Test database deletion failure"""
        mock_collection.find_one.return_value = sample_user_doc
        mock_collection.delete_one.return_value = Mock(
            deleted_count=0
        )  # Failed to delete

        with pytest.raises(RuntimeError, match="Failed to delete user"):
            user_service.delete_user("test-user-id-123")

    # Test authenticate_user method
    def test_authenticate_user_success(self, user_service, mock_collection):
        """Test successful authentication"""
        # Create a user doc with known password hash
        password = "testpassword123"
        hashed_password = UserService._hash_password(password)

        user_doc = {
            "user_id": "test-id",
            "username": "testuser",
            "email": "test@example.com",
            "password": hashed_password,
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "created_at": datetime.now(),
            "last_updated_at": datetime.now(),
        }

        mock_collection.find_one.return_value = user_doc

        result = user_service.authenticate_user("testuser", password)

        assert result is not None
        assert isinstance(result, UserResponse)
        assert result.username == "testuser"
        assert not hasattr(result, "password")  # Password excluded

    def test_authenticate_user_wrong_password(self, user_service, mock_collection):
        """Test authentication with wrong password"""
        password = "testpassword123"
        hashed_password = UserService._hash_password(password)

        user_doc = {
            "username": "testuser",
            "password": hashed_password,
            "email": "test@example.com",
        }

        mock_collection.find_one.return_value = user_doc

        result = user_service.authenticate_user("testuser", "wrongpassword")

        assert result is None

    def test_authenticate_user_not_found(self, user_service, mock_collection):
        """Test authentication with non-existent user"""
        mock_collection.find_one.return_value = None

        result = user_service.authenticate_user("nonexistent", "password")

        assert result is None
