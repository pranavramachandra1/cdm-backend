from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import users

app = FastAPI()

# Include the users router
app.include_router(users.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)