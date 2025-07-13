import pytest

from app.database import cleanup_test_dbs, get_test_user_service
from app.services.users import UserCreate, UserResponse, UserService


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
    def user_service(self):
        return get_test_user_service()

    def test_user_create_get_delete(self, user_service: UserService, user_create_data):

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
