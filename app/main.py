from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .routers import users, lists, tasks
from .dependencies import get_api_key

app = FastAPI(
    title="CarpeDoEm",
    description="Backend for taskmanagement application",
    dependencies=[Depends(get_api_key)]  # Apply API key to all routes
)

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - they inherit the global API key dependency
app.include_router(users.router)
app.include_router(lists.router)
app.include_router(tasks.router)

# Health check endpoint (override global dependency to exclude API key)
@app.get("/health", dependencies=[])
async def health_check():
    return {"status": "healthy", "service": "CarpeDoEm"}

# Root endpoint (also exclude API key)
@app.get("/", dependencies=[])
async def root():
    return {"message": "CarpeDoEm API is running"}