from fastapi import APIRouter, Request
from app.services.users import UserService
from typing import Dict
from app.services.task import TaskService

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

# CRUD operations for tasks

