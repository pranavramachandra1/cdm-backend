from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import users, lists, tasks

app = FastAPI()

app.include_router(users.router)
app.include_router(lists.router)
app.include_router(tasks.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost",
    ],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
