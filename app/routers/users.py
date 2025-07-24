from fastapi import APIRouter, Request
from app.services.users import UserService
from typing import Dict
from fastapi import FastAPI, HTTPException, Depends
from functools import wraps

from app.services.users import *
from app.dependencies import get_user_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


def handle_exceptions(func):
    """
    Wrapper for exception hanlding
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except UserAlreadyExistsError as e:
            raise HTTPException(status_code=409, detail="User already exists")
        except UserNotFoundError as e:
            raise HTTPException(status_code=404, detail="User not found")
        except InvalidCredentialsError as e:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        except NoFieldsToUpdateError as e:
            raise HTTPException(status_code=400, detail="No fields to update")

    return wrapper


# CRUD operations for users


@router.post("/", response_model=UserResponse)
@handle_exceptions
async def create_user(
    user_data: UserCreate, user_service: UserService = Depends(get_user_service)
):
    return user_service.create_user(user_data)


@router.post("/create-test-user", response_model=UserResponse)
@handle_exceptions
async def create_user(
    user_service: UserService = Depends(get_user_service)
):
    return user_service.create_user(UserCreate(
        username="johndoe123",
        email="johndoe123@gmail.com",
        password="lmao123",
        phone_number="8477320621",
        first_name="John",
        last_name="Doe",
        google_id="bruhski123",
    ))


@router.get("/{user_id}", response_model=UserResponse)
@handle_exceptions
async def get_user(user_id: str, user_service: UserService = Depends(get_user_service)):
    return user_service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
@handle_exceptions
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    return user_service.update_user(user_id, user_data)


@router.delete("/{user_id}")
@handle_exceptions
async def delete_user(
    user_id: str, user_service: UserService = Depends(get_user_service)
):
    return user_service.delete_user(user_id)


@router.post("/auth/{user_id}")
@handle_exceptions
async def authenticate_user(
    user_id: str, user_service: UserService = Depends(get_user_service)
):
    return user_service.authenticate_user()

@router.get("/google-id/{google_id}", response_model=UserResponse)
@handle_exceptions
async def get_user_with_google_id(google_id: str, user_service: UserService = Depends(get_user_service)):
    return user_service.get_user_with_google_id(google_id)
