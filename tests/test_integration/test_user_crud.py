import pytest
from datetime import datetime

from app.database import cleanup_test_dbs, get_test_user_service
from app.services.users import (
    UserCreate,
    UserResponse,
    UserService,
    UserUpdate,
    UserNotFoundError,
    UserAlreadyExistsError,
    NoFieldsToUpdateError,
)


class TestUserCrud:
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
    def user_update_data(self):
        return UserUpdate(email="helloworld123@gmail.com")

    @pytest.fixture
    def user_dual_update_data(self):
        return UserUpdate(email="helloworld123@gmail.com", first_name="Peter")

    @pytest.fixture
    def user_service(self):
        return get_test_user_service()

    def test_user_create_get_delete(
        self, user_service: UserService, user_create_data: UserCreate
    ):

        # Create user:
        user_create_response = user_service.create_user(user_data=user_create_data)

        # Check if ground-truth response model is correct:
        assert user_create_response.username == "johndoe123", "Username is not correct"
        assert (
            user_create_response.email == "johndoe123@gmail.com"
        ), "Email is not correct"
        assert (
            user_create_response.phone_number == "(847)-732-0621"
        ), "Phone number is not correct"
        assert user_create_response.first_name == "John", "First name is not correct"
        assert user_create_response.last_name == "Doe", "Last name is not correct"

        # Retrieve user:
        user_get_response = user_service.get_user(user_id=user_create_response.user_id)

        user_create_response_dict = user_create_response.model_dump()
        user_get_response_dict = user_get_response.model_dump()

        assert (
            user_create_response_dict == user_get_response_dict
        ), "Inconsistency between create and get models"

        # Delete user:
        delete_response = user_service.delete_user(
            user_id=user_get_response_dict["user_id"]
        )
        with pytest.raises(UserNotFoundError):
            user_service.get_user(user_id=user_create_response_dict["user_id"])

    def test_user_edit_single_entry(
        self,
        user_service: UserService,
        user_create_data: UserCreate,
        user_update_data: UserUpdate,
    ):
        """
        Testing user update functionality
        """

        # Create user
        user_create_response = user_service.create_user(user_data=user_create_data)

        # Edit user
        update_time = datetime.now()
        user_updated_response = user_service.update_user(
            user_create_response.user_id, user_update_data
        )

        # Compare results
        user_create_response_data = user_create_response.model_dump()
        user_updated_response_data = user_updated_response.model_dump()

        # Check if email and last_updated_at updated correctly
        assert (
            user_update_data.email == "helloworld123@gmail.com"
        ), "Email was not updated properly"

        # Check if all other fields reamin the same:
        assert (
            user_create_response_data["user_id"]
            == user_updated_response_data["user_id"]
        ), "ID was updated"
        assert (
            user_create_response_data["username"]
            == user_updated_response_data["username"]
        ), "ID was updated"
        assert (
            user_create_response_data["phone_number"]
            == user_updated_response_data["phone_number"]
        ), "ID was updated"
        assert (
            user_create_response_data["first_name"]
            == user_updated_response_data["first_name"]
        ), "ID was updated"
        assert (
            user_create_response_data["last_name"]
            == user_updated_response_data["last_name"]
        ), "ID was updated"
        assert (
            user_create_response_data["created_at"]
            == user_updated_response_data["created_at"]
        ), "ID was updated"

    def test_user_edit_dual_entry(
        self,
        user_service: UserService,
        user_create_data: UserCreate,
        user_dual_update_data: UserUpdate,
    ):
        """
        Testing user update functionality on 2+ parameters
        """

        # Create user
        user_create_response = user_service.create_user(user_data=user_create_data)

        # Edit user
        update_time = datetime.now()
        user_updated_response = user_service.update_user(
            user_create_response.user_id, user_dual_update_data
        )

        # Compare results
        user_create_response_data = user_create_response.model_dump()
        user_updated_response_data = user_updated_response.model_dump()

        # Check if email and last_updated_at updated correctly
        assert (
            user_dual_update_data.email == "helloworld123@gmail.com"
        ), "Email was not updated properly"
        assert (
            user_dual_update_data.first_name == "Peter"
        ), "ID was not updated properly"

        # Check if all other fields reamin the same:
        assert (
            user_create_response_data["user_id"]
            == user_updated_response_data["user_id"]
        ), "ID was updated"
        assert (
            user_create_response_data["username"]
            == user_updated_response_data["username"]
        ), "username was updated"
        assert (
            user_create_response_data["phone_number"]
            == user_updated_response_data["phone_number"]
        ), "phone_number was updated"
        assert (
            user_create_response_data["last_name"]
            == user_updated_response_data["last_name"]
        ), "last name was updated"
        assert (
            user_create_response_data["created_at"]
            == user_updated_response_data["created_at"]
        ), "create_at was updated"

    def test_user_crud_exception_handling(
        self, user_service: UserService, user_create_data: UserCreate
    ):
        """Test exception handling in user CRUD operations"""

        # Test UserNotFoundError for get_user
        with pytest.raises(UserNotFoundError, match="User not found"):
            user_service.get_user("nonexistent-user-id")

        # Test UserNotFoundError for update_user
        with pytest.raises(UserNotFoundError, match="User not found"):
            user_service.update_user(
                "nonexistent-user-id", UserUpdate(first_name="Test")
            )

        # Test UserNotFoundError for delete_user
        with pytest.raises(UserNotFoundError, match="User not found"):
            user_service.delete_user("nonexistent-user-id")

        # Create user for remaining tests
        user_response = user_service.create_user(user_data=user_create_data)

        # Test UserAlreadyExistsError
        with pytest.raises(UserAlreadyExistsError, match="User already exists"):
            user_service.create_user(user_data=user_create_data)

        # Test NoFieldsToUpdateError
        with pytest.raises(NoFieldsToUpdateError, match="No fields to update"):
            user_service.update_user(user_response.user_id, UserUpdate())

        # Clean up
        user_service.delete_user(user_response.user_id)

    def test_user_validation_edge_cases(self, user_service: UserService):
        """Test user data validation edge cases"""

        # Test invalid email formats
        with pytest.raises(ValueError, match="Invalid email format"):
            UserCreate(
                username="testuser",
                email="invalid-email-no-at",
                password="password123",
                phone_number="+1234567890",
                first_name="Test",
                last_name="User",
                google_id="test-google-id",
            )

        with pytest.raises(ValueError, match="Invalid email format"):
            UserCreate(
                username="testuser",
                email="",  # Empty email
                password="password123",
                phone_number="+1234567890",
                first_name="Test",
                last_name="User",
                google_id="test-google-id",
            )

        # Test that valid email passes validation
        valid_user = UserCreate(
            username="validuser",
            email="valid@example.com",
            password="password123",
            phone_number="+1234567890",
            first_name="Test",
            last_name="User",
            google_id="test-google-id",
        )

        user_response = user_service.create_user(user_data=valid_user)
        assert user_response.email == "valid@example.com"

        # Clean up
        user_service.delete_user(user_response.user_id)
