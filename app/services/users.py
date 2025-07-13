# app/services/users.py
import uuid
from datetime import datetime
from typing import Optional
from passlib.context import CryptContext
from pydantic import BaseModel, field_validator, ValidationInfo, ValidationError

from pymongo import collection as PyMongoCollection

# Keep your existing Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    phone_number: str
    first_name: str
    last_name: str
    google_id: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v, info: ValidationInfo):
        if not v or '@' not in v:
            raise ValueError('Invalid email format')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    google_id: Optional[str] = None

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    phone_number: str
    first_name: str
    last_name: str
    created_at: datetime
    last_updated_at: datetime

# Custom exceptions (instead of HTTPException in business logic)
class UserAlreadyExistsError(Exception):
    pass

class UserNotFoundError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass

class NoFieldsToUpdateError(Exception):
    pass

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """
    Improved design for testability:
    1. Database dependency injection
    2. Separate business logic from HTTP concerns
    3. Custom exceptions instead of HTTPException
    """
    
    def __init__(self, user_collection:PyMongoCollection = None):
        # Dependency injection - can pass in mock for testing
        self.user_collection = user_collection

    @staticmethod
    def _hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def _verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_user_id() -> str:
        return str(uuid.uuid4())

    def user_exists(self, username: str = None, email: str = None, phone_number: str = None, user_id: str = None, google_id: str = None) -> bool:
        """
        Unified method to check if user exists by any combination of fields
        """
        query_conditions = []
        
        if username:
            query_conditions.append({"username": username})
        if email:
            query_conditions.append({"email": email})
        if phone_number:
            query_conditions.append({"phone_number": phone_number})
        if user_id:
            query_conditions.append({"user_id": user_id})
        
        if not query_conditions:
            return False
            
        result = self.user_collection.find_one({"$or": query_conditions})
        return result is not None

    def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Creates a new user with proper validation and error handling
        Business logic only - no HTTP concerns
        """
        # Check if user already exists
        if self.user_exists(
            username=user_data.username, 
            email=user_data.email, 
            phone_number=user_data.phone_number
        ):
            raise UserAlreadyExistsError("User already exists")

        # Create user document
        user_id = self.create_user_id()
        hashed_password = self._hash_password(user_data.password)
        
        user_doc = {
            "user_id": user_id,
            "username": user_data.username,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "email": user_data.email,
            "password": hashed_password,
            "phone_number": user_data.phone_number,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # only grab up until seconds
            "last_updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "google_id": user_data.google_id
        }
        
        self.user_collection.insert_one(user_doc)
        
        # Return user without password
        return UserResponse(**{k: v for k, v in user_doc.items() if k != 'password'})

    def get_user(self, user_id: str) -> UserResponse:
        """
        Retrieves a user by ID
        """
        user = self.user_collection.find_one({"user_id": user_id})
        
        if not user:
            raise UserNotFoundError("User not found")
        
        # Remove password from response
        user_data = {k: v for k, v in user.items() if k != 'password'}
        return UserResponse(**user_data)

    def update_user(self, user_id: str, user_data: UserUpdate) -> UserResponse:
        """
        Updates user with only provided fields
        """
        if not self.user_exists(user_id=user_id):
            raise UserNotFoundError("User not found")
        
        # Get only fields that were actually provided
        update_data = user_data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise NoFieldsToUpdateError("No fields to update")
        
        # Add timestamp
        update_data["last_updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update in database
        self.user_collection.update_one(
            {"user_id": user_id}, 
            {"$set": update_data}
        )
        
        return self.get_user(user_id)

    def delete_user(self, user_id: str) -> dict:
        """
        Deletes a user by ID
        """
        if not self.user_exists(user_id=user_id):
            raise UserNotFoundError("User not found")
        
        result = self.user_collection.delete_one({"user_id": user_id})
        
        if result.deleted_count == 0:
            raise RuntimeError("Failed to delete user")
        
        return {"message": "User deleted successfully"}

    def authenticate_user(self, username: str, password: str) -> Optional[UserResponse]:
        """
        Authenticates a user by username and password
        Returns None for invalid credentials (instead of raising exception)
        """
        user = self.user_collection.find_one({"username": username})
        
        if not user or not self._verify_password(password, user["password"]):
            return None
        
        user_data = {k: v for k, v in user.items() if k != 'password'}
        return UserResponse(**user_data)
    
    def google_authenticate_user(self,  username: str = None, email: str = None, phone_number: str = None, user_id: str = None, google_id: str = None) -> bool:
        """Passes result to authenticate user for GoogleAuth"""

        if not self.user_exists(
            username=username,
            email=email,
            phone_number=phone_number,
            user_id=user_id,
            google_id=google_id
        ):
            raise UserNotFoundError("User does not exist")
        
        return True