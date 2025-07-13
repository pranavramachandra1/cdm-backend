from fastapi import APIRouter, Request
from app.services.users import UserService
from typing import Dict
from fastapi import FastAPI, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

from app.services.users import UserService, UserNotFoundError
from app.services.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def handle_exceptions(func):
    """
    Wrapper for exception hanlding
    """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except UserNotFoundError as e:
            raise HTTPException(status_code=404, detail="User not found")

    return wrapper


user_service = UserService()


@router.post("/google")
@handle_exceptions
async def google_auth(google_token: str):
    # Verify the Google token
    idinfo = id_token.verify_oauth2_token(
        google_token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
    )

    # Extract user info from verified token
    google_id = idinfo["sub"]
    username = idinfo["username"]
    email = idinfo["email"]
    phone_number = idinfo["phone_number"]
    user_id = idinfo["user_id"]

    # Authenticate user interally
    user_service.google_authenticate_user(
        username=username,
        email=email,
        phone_number=phone_number,
        user_id=user_id,
        google_id=google_id,
    )

    # Create your own JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
