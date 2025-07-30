from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import logging
from functools import wraps

from app.services.task import (
    TaskService,
    TaskResponse,
    TaskCreate,
    TaskUpdate,
    FailedToDeleteTaskError,
    TaskNotFoundError,
    InvalidVersionRequest,
    ToggleIncompleteError,
    NoTasksToRemove,
)
from app.dependencies import get_task_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def handle_task_exceptions(func):
    """
    Decorator for handling task service exceptions
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except TaskNotFoundError as e:
            logger.warning(f"Task not found in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        except FailedToDeleteTaskError as e:
            logger.error(f"Failed to delete task in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete task",
            )

        except InvalidVersionRequest as e:
            logger.warning(f"Invalid version request in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,  # 400, not 401
                detail="Invalid version requested",
            )

        except ToggleIncompleteError as e:
            logger.warning(f"Toggle was unsuccessful in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,  # 400, not 401
                detail="Unable to toggle complete on task",
            )

        except NoTasksToRemove as e:
            logger.warning(f"No tasks to removed during {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,  # 400, not 401
                detail="Unable to toggle complete on task",
            )

        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )

    return wrapper


# Initialize service

# ========================================
# CRUD OPERATIONS
# ========================================


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@handle_task_exceptions
async def create_task(
    task_data: TaskCreate, task_service: TaskService = Depends(get_task_service)
):  # ✅ Fixed typo: create_take -> create_task
    """Create a new task"""
    return task_service.create_task(task_data)


@router.get("/{task_id}", response_model=TaskResponse)
@handle_task_exceptions
async def get_task(task_id: str, task_service: TaskService = Depends(get_task_service)):
    """Get a task by ID"""
    return task_service.get_task(task_id)


@router.put("/{task_id}", response_model=TaskResponse)
@handle_task_exceptions
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    task_service: TaskService = Depends(get_task_service),
):
    """Update a task by ID"""
    return task_service.update_task(task_id=task_id, task_data=task_data)


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
@handle_task_exceptions
async def delete_task(
    task_id: str, task_service: TaskService = Depends(get_task_service)
):
    """Delete a task by ID"""
    return task_service.delete_task(task_id)


# ========================================
# TASK STATE OPERATIONS
# ========================================


@router.patch("/toggle-complete/{task_id}", response_model=TaskResponse)
@handle_task_exceptions
async def toggle_completion(
    task_id: str, task_service: TaskService = Depends(get_task_service)
):
    """Toggle task completion status"""
    return task_service.toggle_completion(task_id)


@router.patch("/toggle-recurring/{task_id}", response_model=TaskResponse)
@handle_task_exceptions
async def toggle_recurring(
    task_id: str, task_service: TaskService = Depends(get_task_service)
):
    """Toggle task reccurance status"""
    return task_service.toggle_recurring(task_id)


@router.patch("/toggle-priority/{task_id}", response_model=TaskResponse)
@handle_task_exceptions
async def toggle_priority(
    task_id: str, task_service: TaskService = Depends(get_task_service)
):
    """Toggle task priority status"""
    return task_service.toggle_priority(task_id)


# ========================================
# LIST OPERATIONS
# ========================================


@router.post("/clear-list/{list_id}", response_model=List[TaskResponse])
@handle_task_exceptions
async def clear_list(
    list_id: str, task_service: TaskService = Depends(get_task_service)
):
    """Clear all tasks from a list"""
    return task_service.clear_list(list_id)


@router.post("/rollover-list/{list_id}", response_model=List[TaskResponse])
@handle_task_exceptions
async def rollover_list(
    list_id: str, task_service: TaskService = Depends(get_task_service)
):
    """Create new version of list with incomplete tasks"""
    return task_service.rollover_list(list_id)


# ========================================
# QUERY OPERATIONS
# ========================================


@router.get(
    "/list/{list_id}/current", response_model=List[TaskResponse]
)  # Better URL structure
@handle_task_exceptions
async def get_current_tasks_from_list(
    list_id: str, task_service: TaskService = Depends(get_task_service)
):
    """Get current tasks from a list"""
    return task_service.get_current_tasks_from_list(list_id)


@router.get(
    "/list/{list_id}/version/{list_request_version}",
    response_model=List[TaskResponse],
)  # Cleaner URL
@handle_task_exceptions
async def get_tasks_from_list_version(
    list_id: str,
    list_request_version: int,
    task_service: TaskService = Depends(get_task_service),
):
    """Get versions of a list with pagination"""
    return task_service.get_tasks_from_list_version(
        list_id=list_id,
        list_request_version=list_request_version,
    )
