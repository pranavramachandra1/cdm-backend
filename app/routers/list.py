from fastapi import APIRouter, HTTPException, status, Depends
from app.services.lists import (
    ListService,
    ListResponse,
    ListCreate,
    ListUpdate,
    ListNotFoundError,
    FailedToDeleteList,
    InvalidParameters,
    NoFieldsToUpdateError,
)
from typing import List
import logging

from app.dependencies import get_list_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lists", tags=["lists"])


def handle_list_exceptions(func):
    """
    Decorator for handling list service exceptions
    """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except ListNotFoundError as e:
            logger.warning(f"List not found in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="List not found"
            )

        except FailedToDeleteList as e:
            logger.error(f"Failed to delete list in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete list",
            )

        except InvalidParameters as e:
            logger.warning(f"Invalid parameters in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,  # ✅ Changed from 401 to 400
                detail="Invalid parameters provided",
            )

        except NoFieldsToUpdateError as e:
            logger.warning(f"No fields to update in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )

    return wrapper


# ========================================
# CRUD OPERATIONS
# ========================================


@router.post("/", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
@handle_list_exceptions
async def create_list(
    list_data: ListCreate, list_service: ListService = Depends(get_list_service)
):
    """Create a new list"""
    return list_service.create_list(list_data)


@router.get("/{list_id}", response_model=ListResponse)
@handle_list_exceptions
async def get_list(list_id: str, list_service: ListService = Depends(get_list_service)):
    """Get a list by ID"""
    return list_service.get_list(list_id=list_id)  # ✅ Kept your parameter style


@router.put("/{list_id}", response_model=ListResponse)
@handle_list_exceptions
async def update_list(
    list_id: str,
    list_data: ListUpdate,
    list_service: ListService = Depends(get_list_service),
):
    """Update a list by ID"""
    return list_service.update_list(list_id, list_data)


@router.delete("/{list_id}", status_code=status.HTTP_200_OK)
@handle_list_exceptions
async def delete_list(
    list_id: str, list_service: ListService = Depends(get_list_service)
):
    """Delete a list by ID"""
    result = list_service.delete_list(list_id)
    # ✅ Changed: DELETE typically returns success message, not the deleted object
    return {"message": "List deleted successfully", "list_id": list_id}


# ========================================
# USER-RELATED OPERATIONS
# ========================================


@router.get(
    "/user/{user_id}", response_model=List[ListResponse]
)  # ✅ Better URL structure
@handle_list_exceptions
async def get_lists_by_user(
    user_id: str, list_service: ListService = Depends(get_list_service)
):
    """Get all lists belonging to a user"""
    return list_service.get_lists_by_user(user_id)


# ========================================
# LIST VERSION OPERATIONS
# ========================================


@router.patch(
    "/{list_id}/increment-version", response_model=ListResponse
)  # ✅ Better URL structure
@handle_list_exceptions
async def increment_list_version(
    list_id: str, list_service: ListService = Depends(get_list_service)
):
    """Increment the version of a list"""
    return list_service.increment_version(list_id)


# ========================================
# ADDITIONAL USEFUL ENDPOINTS
# ========================================


@router.get("/", response_model=List[ListResponse])
@handle_list_exceptions
async def get_all_lists(
    skip: int = 0,
    limit: int = 100,
    user_id: str = None,
    list_service: ListService = Depends(get_list_service),  # Optional filter by user
):
    """
    Get all lists with optional pagination and filtering
    """
    if user_id:
        return list_service.get_lists_by_user(user_id)
    else:
        return list_service.get_all_lists(skip=skip, limit=limit)


@router.get("/{list_id}/stats")
@handle_list_exceptions
async def get_list_statistics(
    list_id: str, list_service: ListService = Depends(get_list_service)
):
    """
    Get statistics for a list (total tasks, completed tasks, etc.)
    """
    return list_service.get_list_statistics(list_id)
