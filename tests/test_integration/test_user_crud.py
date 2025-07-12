import pytest
from datetime import datetime

from app.routers.users import create_user, get_user
from app.services.users import UserCreate, UserUpdate, UserResponse
from app.database import get_test_user_service, get_test_list_service, get_test_task_service, cleanup
from app.dependencies import get_mongo_db

class TestUserCrud:

    """
    Testing CRUD functionalities for CRUD operations
    related to users
    """    

    @pytest.fixture(autouse=True)
    async def run_cleanup(self, mock_user_service):
        """
        Automatically runs cleanup after each test function.
        """
        print("run_cleanup fixture started")
        yield
        print("run_cleanup fixture running cleanup")
        await cleanup(user_service=mock_user_service)
        print("run_cleanup fixture completed")
    
    @pytest.fixture
    def mock_user_create(self):
        return UserCreate(
            username = "username1",
            email = "johndoe123@gmail.com",
            password = "password",
            phone_number = "(847)-732-0621",
            first_name = "John",
            last_name = "Doe",
            google_id = "test123"
        )
    
    @pytest.fixture
    def mock_user_service(self):
        """
        Returns the test user service
        """
        return get_test_user_service()
    
    # @pytest.mark.asyncio
    # async def test_cleanup(self, mock_user_service, mock_user_create):
    #     user_response = await create_user(user_data=mock_user_create, user_service=mock_user_service)
    #     # Collection should exist
    #     assert mock_user_service.user_collection.name in get_mongo_db().list_collection_names()
    #     # Run cleanup explicitly
    #     await cleanup(user_service=mock_user_service)
    #     # Collection should be gone
    #     assert mock_user_service.user_collection.name not in get_mongo_db().list_collection_names()
    
    @pytest.mark.asyncio
    @pytest.mark.usefixtures('run_cleanup')
    async def test_create_get_user(self, mock_user_create, mock_user_service):
        """
        Tests creation and deletion of 
        """

        # create user:

        user_response = await create_user(user_data = mock_user_create, user_service=mock_user_service)

        # check if user data is correct:
        assert user_response.username == "username1", "Username is incorrect"
        assert user_response.email == "johndoe123@gmail.com", "Email is incorrect"
        assert user_response.phone_number == "(847)-732-0621", "Phone number is incorrect"
        assert user_response.first_name == "John", "First name is incorrect"
        assert user_response.last_name == "Doe", "Last name is incorrect"

        # breakpoint()

        # get user again
        get_user_response = await get_user(user_response.user_id, user_service=mock_user_service)

        # breakpoint()

        # assert user_response == get_user_response, "Responses are not equivalent"

        # breakpoint()

        return