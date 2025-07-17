# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
python run.py
```
The server runs on `http://0.0.0.0:8080` using uvicorn.

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test files
python -m pytest tests/test_integration/test_user_crud.py
python -m pytest tests/test_services/test_user_service.py

# Run tests with verbose output
python -m pytest -v
```

### Dependencies
Install dependencies using:
```bash
pip install -r requirements.txt
```

Note: The requirements.txt file is currently empty but this is the expected pattern for this project.

## Architecture Overview

This is a **FastAPI-based todo/task management backend** with the following structure:

### Core Architecture
- **FastAPI** web framework with CORS middleware configured for frontend on `localhost:3000`
- **MongoDB** database with PyMongo client
- **Service layer pattern** separating business logic from API routes
- **Comprehensive testing** with both unit tests (mocked) and integration tests (real DB)

### Key Components

**App Structure:**
- `app/main.py` - FastAPI application entry point
- `app/routers/` - API route handlers (users, auth, lists, tasks)
- `app/services/` - Business logic layer (UserService, ListService, TaskService)
- `app/database.py` - Database connection and test utilities
- `app/dependencies.py` - Dependency injection setup
- `run.py` - Application runner

**Services:**
- **UserService** - User CRUD operations, authentication, password hashing
- **ListService** - Todo list management
- **TaskService** - Task operations within lists

### Testing Strategy

**Integration Tests** (`tests/test_integration/`):
- Use real MongoDB collections with auto-generated test collection names
- Include automatic cleanup via `cleanup_test_dbs()` function
- Test full CRUD workflows end-to-end

**Unit Tests** (`tests/test_services/`):
- Mock MongoDB collections for isolated testing
- Test individual service methods in isolation
- Comprehensive coverage of edge cases and error conditions

**Test Utilities:**
- `get_test_collection()` - Creates uniquely named test collections
- `get_test_user_service()` - Factory for test user service instances
- `cleanup_test_dbs()` - Removes all test collections after test runs

### Database Design
- Uses **MongoDB** with PyMongo
- Test collections are prefixed with `test-` and include timestamps for uniqueness
- Production and test databases are handled via dependency injection

### Key Patterns
- **Pydantic models** for request/response validation (UserCreate, UserUpdate, UserResponse)
- **Custom exceptions** for business logic errors (UserNotFoundError, UserAlreadyExistsError)
- **Password hashing** with bcrypt for security
- **Service layer** pattern keeping business logic separate from API routes