import pytest
from datetime import datetime
from pydantic import ValidationError

from app.database import cleanup_test_dbs, get_services
from app.services.users import (
    UserService,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserAlreadyExistsError,
    UserNotFoundError,
    NoFieldsToUpdateError,
)
from app.services.lists import ListService, ListCreate
from app.services.task import TaskService, TaskCreate


class TestAuthOperations:
    """
    Comprehensive integration tests for authentication, authorization, and user management edge cases
    """

    @pytest.fixture(scope="session", autouse=True)
    def cleanup(self):
        yield
        cleanup_test_dbs()

    @pytest.fixture
    def services(self):
        return get_services()

    @pytest.fixture
    def valid_user_data(self):
        return UserCreate(
            username="testuser123",
            email="testuser123@gmail.com",
            password="securepassword123",
            phone_number="(555)-123-4567",
            first_name="Test",
            last_name="User",
            google_id="test-google-id",
        )

    def test_user_authentication_success(self, services, valid_user_data: UserCreate):
        """Test successful user authentication"""
        user_service: UserService = services["user_service"]

        # Create user
        user_response = user_service.create_user(user_data=valid_user_data)

        # Test successful authentication
        auth_result = user_service.authenticate_user(
            username=valid_user_data.username, password=valid_user_data.password
        )

        assert auth_result is not None
        assert isinstance(auth_result, UserResponse)
        assert auth_result.username == valid_user_data.username
        assert auth_result.email == valid_user_data.email
        assert auth_result.user_id == user_response.user_id

        # Verify password is not included in response
        assert not hasattr(auth_result, "password")

    def test_user_authentication_failures(self, services, valid_user_data: UserCreate):
        """Test authentication failure scenarios"""
        user_service: UserService = services["user_service"]

        # Create user
        user_service.create_user(user_data=valid_user_data)

        # Test wrong password
        auth_result = user_service.authenticate_user(
            username=valid_user_data.username, password="wrongpassword"
        )
        assert auth_result is None

        # Test non-existent user
        auth_result = user_service.authenticate_user(
            username="nonexistentuser", password=valid_user_data.password
        )
        assert auth_result is None

        # Test empty credentials
        auth_result = user_service.authenticate_user(username="", password="")
        assert auth_result is None

    def test_google_authentication_success(self, services, valid_user_data: UserCreate):
        """Test successful Google authentication"""
        user_service: UserService = services["user_service"]

        # Create user
        user_service.create_user(user_data=valid_user_data)

        # Test Google auth by username
        result = user_service.google_authenticate_user(
            username=valid_user_data.username
        )
        assert result == True

        # Test Google auth by email
        result = user_service.google_authenticate_user(email=valid_user_data.email)
        assert result == True

        # Test Google auth by google_id
        result = user_service.google_authenticate_user(
            google_id=valid_user_data.google_id
        )
        assert result == True

        # Test Google auth by phone_number
        result = user_service.google_authenticate_user(
            phone_number=valid_user_data.phone_number
        )
        assert result == True

    def test_google_authentication_failures(self, services):
        """Test Google authentication failure scenarios"""
        user_service: UserService = services["user_service"]

        # Test non-existent user
        with pytest.raises(UserNotFoundError, match="User does not exist"):
            user_service.google_authenticate_user(username="nonexistent")

        with pytest.raises(UserNotFoundError, match="User does not exist"):
            user_service.google_authenticate_user(email="nonexistent@test.com")

        with pytest.raises(UserNotFoundError, match="User does not exist"):
            user_service.google_authenticate_user(google_id="nonexistent-google-id")

    def test_user_creation_edge_cases(self, services):
        """Test user creation with various edge cases"""
        user_service: UserService = services["user_service"]

        # Test invalid email validation
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="invalid-email",  # No @ symbol
                password="password123",
                phone_number="+1234567890",
                first_name="Test",
                last_name="User",
                google_id="test-google-id",
            )

        # Test empty email validation
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="",  # Empty email
                password="password123",
                phone_number="+1234567890",
                first_name="Test",
                last_name="User",
                google_id="test-google-id",
            )

        # Test valid user creation
        valid_user = UserCreate(
            username="validuser",
            email="valid@example.com",
            password="securepassword123",
            phone_number="+1234567890",
            first_name="Valid",
            last_name="User",
            google_id="valid-google-id",
        )

        user_response = user_service.create_user(user_data=valid_user)
        assert user_response.username == "validuser"
        assert user_response.email == "valid@example.com"

    def test_duplicate_user_creation(self, services, valid_user_data: UserCreate):
        """Test creation of duplicate users with same credentials"""
        user_service: UserService = services["user_service"]

        # Create first user
        user_service.create_user(user_data=valid_user_data)

        # Try to create user with same username
        duplicate_username = UserCreate(
            username=valid_user_data.username,  # Same username
            email="different@example.com",
            password="password123",
            phone_number="(555)-999-8888",
            first_name="Different",
            last_name="User",
            google_id="different-google-id",
        )

        with pytest.raises(UserAlreadyExistsError, match="User already exists"):
            user_service.create_user(user_data=duplicate_username)

        # Try to create user with same email
        duplicate_email = UserCreate(
            username="differentuser",
            email=valid_user_data.email,  # Same email
            password="password123",
            phone_number="(555)-999-8888",
            first_name="Different",
            last_name="User",
            google_id="different-google-id",
        )

        with pytest.raises(UserAlreadyExistsError, match="User already exists"):
            user_service.create_user(user_data=duplicate_email)

        # Try to create user with same phone number
        duplicate_phone = UserCreate(
            username="differentuser2",
            email="different2@example.com",
            password="password123",
            phone_number=valid_user_data.phone_number,  # Same phone
            first_name="Different",
            last_name="User",
            google_id="different-google-id",
        )

        with pytest.raises(UserAlreadyExistsError, match="User already exists"):
            user_service.create_user(user_data=duplicate_phone)

    def test_user_update_edge_cases(self, services, valid_user_data: UserCreate):
        """Test user update operations with edge cases"""
        user_service: UserService = services["user_service"]

        # Create user
        user_response = user_service.create_user(user_data=valid_user_data)

        # Test updating non-existent user
        with pytest.raises(UserNotFoundError, match="User not found"):
            user_service.update_user("nonexistent-id", UserUpdate(first_name="New"))

        # Test updating with no fields
        with pytest.raises(NoFieldsToUpdateError, match="No fields to update"):
            user_service.update_user(user_response.user_id, UserUpdate())

        # Test valid single field update
        updated_user = user_service.update_user(
            user_response.user_id, UserUpdate(first_name="UpdatedFirst")
        )

        assert updated_user.first_name == "UpdatedFirst"
        assert updated_user.last_name == valid_user_data.last_name  # Unchanged
        assert updated_user.email == valid_user_data.email  # Unchanged

        # Test multiple field update
        multi_updated_user = user_service.update_user(
            user_response.user_id,
            UserUpdate(
                first_name="MultiFirst",
                last_name="MultiLast",
                email="multi@example.com",
            ),
        )

        assert multi_updated_user.first_name == "MultiFirst"
        assert multi_updated_user.last_name == "MultiLast"
        assert multi_updated_user.email == "multi@example.com"
        assert multi_updated_user.username == valid_user_data.username  # Unchanged

    def test_user_deletion_edge_cases(self, services, valid_user_data: UserCreate):
        """Test user deletion with edge cases"""
        user_service: UserService = services["user_service"]

        # Test deleting non-existent user
        with pytest.raises(UserNotFoundError, match="User not found"):
            user_service.delete_user("nonexistent-id")

        # Create and delete user
        user_response = user_service.create_user(user_data=valid_user_data)

        delete_response = user_service.delete_user(user_response.user_id)
        assert delete_response["message"] == "User deleted successfully"

        # Verify user is deleted
        with pytest.raises(UserNotFoundError, match="User not found"):
            user_service.get_user(user_response.user_id)

        # Try to delete same user again
        with pytest.raises(UserNotFoundError, match="User not found"):
            user_service.delete_user(user_response.user_id)

    def test_password_security(self, services, valid_user_data: UserCreate):
        """Test password hashing and security"""
        user_service: UserService = services["user_service"]

        # Create user
        user_response = user_service.create_user(user_data=valid_user_data)

        # Test that password is hashed (not stored in plain text)
        # We can't directly access the stored password, but we can verify
        # that authentication works with original password
        auth_result = user_service.authenticate_user(
            valid_user_data.username, valid_user_data.password
        )
        assert auth_result is not None

        # Test that password is not in response
        assert not hasattr(user_response, "password")
        assert not hasattr(auth_result, "password")

        # Test password verification with static methods
        plain_password = "testpassword123"
        hashed_password = UserService._hash_password(plain_password)

        # Verify hash is different from plain text
        assert hashed_password != plain_password
        assert len(hashed_password) > len(plain_password)
        assert hashed_password.startswith("$2b$")  # bcrypt format

        # Verify password verification works
        assert UserService._verify_password(plain_password, hashed_password) == True
        assert UserService._verify_password("wrongpassword", hashed_password) == False

    def test_user_exists_combinations(self, services, valid_user_data: UserCreate):
        """Test user_exists method with various parameter combinations"""
        user_service: UserService = services["user_service"]

        # Create user
        user_response = user_service.create_user(user_data=valid_user_data)

        # Test single parameter checks
        assert user_service.user_exists(username=valid_user_data.username) == True
        assert user_service.user_exists(email=valid_user_data.email) == True
        assert (
            user_service.user_exists(phone_number=valid_user_data.phone_number) == True
        )
        assert user_service.user_exists(user_id=user_response.user_id) == True
        assert user_service.user_exists(google_id=valid_user_data.google_id) == True

        # Test with non-existent values
        assert user_service.user_exists(username="nonexistent") == False
        assert user_service.user_exists(email="nonexistent@test.com") == False
        assert user_service.user_exists(phone_number="(999)-999-9999") == False
        assert user_service.user_exists(user_id="nonexistent-id") == False
        assert user_service.user_exists(google_id="nonexistent-google-id") == False

        # Test multiple parameter combinations
        assert (
            user_service.user_exists(
                username=valid_user_data.username, email=valid_user_data.email
            )
            == True
        )

        # Test mixed existing/non-existing (should return True if ANY exists)
        assert (
            user_service.user_exists(
                username=valid_user_data.username,  # Exists
                email="nonexistent@test.com",  # Doesn't exist
            )
            == True
        )

        # Test all non-existing
        assert (
            user_service.user_exists(
                username="nonexistent", email="nonexistent@test.com"
            )
            == False
        )

        # Test no parameters
        assert user_service.user_exists() == False

    def test_cross_service_authorization(self, services, valid_user_data: UserCreate):
        """Test authorization across different services"""
        user_service: UserService = services["user_service"]
        list_service: ListService = services["list_service"]
        task_service: TaskService = services["task_service"]

        # Create two users
        user1_response = user_service.create_user(user_data=valid_user_data)

        user2_data = UserCreate(
            username="user2",
            email="user2@test.com",
            password="password123",
            phone_number="(555)-987-6543",
            first_name="User",
            last_name="Two",
            google_id="user2-google-id",
        )
        user2_response = user_service.create_user(user_data=user2_data)

        # Create list for user1
        list_data = ListCreate(user_id=user1_response.user_id, list_name="User1's List")
        list_response = list_service.create_list(list_data=list_data)

        # Try to create task for user2 in user1's list (should work - no cross-validation)
        task_data = TaskCreate(
            user_id=user2_response.user_id,
            list_id=list_response.list_id,
            task_name="Cross-user task",
            reminders=[],
            isPriority=False,
            isRecurring=False,
            list_version=list_response.version,
        )

        # This should succeed (services don't cross-validate ownership)
        task_response = task_service.create_task(task_data=task_data)
        assert task_response.user_id == user2_response.user_id
        assert task_response.list_id == list_response.list_id

    def test_user_id_generation_uniqueness(self, services):
        """Test that user ID generation produces unique IDs"""
        user_service: UserService = services["user_service"]

        # Generate multiple user IDs and verify uniqueness
        generated_ids = set()
        for i in range(100):
            user_id = UserService.create_user_id()
            assert (
                user_id not in generated_ids
            ), f"Duplicate user ID generated: {user_id}"
            generated_ids.add(user_id)
            assert isinstance(user_id, str)
            assert len(user_id) > 20  # UUID should be reasonably long

    def test_timestamp_handling(self, services, valid_user_data: UserCreate):
        """Test timestamp creation and updates"""
        user_service: UserService = services["user_service"]

        # Create user and verify timestamps
        creation_time = datetime.now()
        user_response = user_service.create_user(user_data=valid_user_data)

        # Verify created_at and last_updated_at are set
        assert user_response.created_at is not None
        assert user_response.last_updated_at is not None
        assert user_response.created_at == user_response.last_updated_at

        # Update user and verify last_updated_at changes
        import time

        time.sleep(1)  # Ensure timestamp difference

        updated_user = user_service.update_user(
            user_response.user_id, UserUpdate(first_name="Updated")
        )

        assert updated_user.created_at == user_response.created_at  # Should not change
        assert (
            updated_user.last_updated_at != user_response.last_updated_at
        )  # Should change
