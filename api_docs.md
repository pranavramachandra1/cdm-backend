# Todo API Documentation

This document provides comprehensive API documentation for the FastAPI-based todo/task management backend.

## Base URL
`http://0.0.0.0:8080`

## Authentication Routes (`/auth`)

### POST `/auth/google`
**Purpose:** Authenticates users via Google OAuth token and returns JWT access token.

**Parameters:**
- `google_token` (string): Google OAuth2 token

**Returns:**
- `access_token` (string): JWT token for API access
- `token_type` (string): Token type ("bearer")

**Status Codes:**
- 200: Success
- 404: User not found

---

## User Routes (`/users`)

### POST `/users/`
**Purpose:** Creates a new user account with required profile information.

**Parameters:**
- Body: `UserCreate`
  - `username` (string): Unique username
  - `email` (string): Valid email address
  - `password` (string): User password
  - `phone_number` (string): Phone number
  - `first_name` (string): First name
  - `last_name` (string): Last name
  - `google_id` (string): Google account ID

**Returns:** `UserResponse`
- `user_id` (string): Unique user identifier
- `username` (string): Username
- `email` (string): Email address
- `phone_number` (string): Phone number
- `first_name` (string): First name
- `last_name` (string): Last name
- `created_at` (datetime): Account creation timestamp
- `last_updated_at` (datetime): Last update timestamp

**Status Codes:**
- 201: User created successfully
- 409: User already exists

### POST `/users/create-test-user`
**Purpose:** Creates a predefined test user for development purposes.

**Parameters:** None

**Returns:** `UserResponse` (same as above)

**Status Codes:**
- 201: Test user created successfully
- 409: User already exists

### GET `/users/{user_id}`
**Purpose:** Retrieves user information by user ID.

**Parameters:**
- `user_id` (string, path): Unique user identifier

**Returns:** `UserResponse` (same structure as POST /users/)

**Status Codes:**
- 200: Success
- 404: User not found

### PUT `/users/{user_id}`
**Purpose:** Updates existing user information with provided fields.

**Parameters:**
- `user_id` (string, path): Unique user identifier
- Body: `UserUpdate`
  - `username` (string, optional): New username
  - `email` (string, optional): New email address
  - `phone_number` (string, optional): New phone number
  - `first_name` (string, optional): New first name
  - `last_name` (string, optional): New last name
  - `google_id` (string, optional): New Google account ID

**Returns:** `UserResponse` (updated user data)

**Status Codes:**
- 200: User updated successfully
- 400: No fields to update
- 404: User not found

### DELETE `/users/{user_id}`
**Purpose:** Permanently deletes a user account and associated data.

**Parameters:**
- `user_id` (string, path): Unique user identifier

**Returns:** Success message

**Status Codes:**
- 200: User deleted successfully
- 404: User not found

### POST `/users/auth/{user_id}`
**Purpose:** Authenticates a user account (legacy endpoint).

**Parameters:**
- `user_id` (string, path): Unique user identifier

**Returns:** Authentication result

**Status Codes:**
- 200: Authentication successful
- 401: Invalid credentials
- 404: User not found

### GET `/users/google-id/{google_id}`
**Purpose:** Retrieves user information using Google account ID.

**Parameters:**
- `google_id` (string, path): Google account identifier

**Returns:** `UserResponse` (same structure as GET /users/{user_id})

**Status Codes:**
- 200: Success
- 404: User not found

---

## List Routes (`/lists`)

### POST `/lists/`
**Purpose:** Creates a new todo list for a user.

**Parameters:**
- Body: `ListCreate`
  - `user_id` (string): Owner's user ID
  - `list_name` (string): Name for the list

**Returns:** `ListResponse`
- `list_id` (string): Unique list identifier
- `user_id` (string): Owner's user ID
- `list_name` (string): List name
- `created_at` (datetime): Creation timestamp
- `last_updated_at` (datetime): Last update timestamp
- `version` (int): List version number

**Status Codes:**
- 201: List created successfully
- 400: Invalid parameters

### GET `/lists/{list_id}`
**Purpose:** Retrieves a specific list by its ID.

**Parameters:**
- `list_id` (string, path): Unique list identifier

**Returns:** `ListResponse` (same structure as POST /lists/)

**Status Codes:**
- 200: Success
- 404: List not found

### PUT `/lists/{list_id}`
**Purpose:** Updates an existing list's properties.

**Parameters:**
- `list_id` (string, path): Unique list identifier
- Body: `ListUpdate`
  - `list_id` (string, optional): New list ID
  - `user_id` (string, optional): New owner ID
  - `list_name` (string, optional): New list name
  - `created_at` (datetime, optional): Creation time
  - `last_updated_at` (datetime, optional): Update time
  - `version` (int, optional): Version number

**Returns:** `ListResponse` (updated list data)

**Status Codes:**
- 200: List updated successfully
- 400: No fields to update or invalid parameters
- 404: List not found

### DELETE `/lists/{list_id}`
**Purpose:** Permanently deletes a list and all associated tasks.

**Parameters:**
- `list_id` (string, path): Unique list identifier

**Returns:**
- `message` (string): Success message
- `list_id` (string): ID of deleted list

**Status Codes:**
- 200: List deleted successfully
- 404: List not found
- 500: Failed to delete list

### GET `/lists/user/{user_id}`
**Purpose:** Retrieves all lists belonging to a specific user.

**Parameters:**
- `user_id` (string, path): User identifier

**Returns:** Array of `ListResponse` objects

**Status Codes:**
- 200: Success
- 404: User not found

### PATCH `/lists/{list_id}/increment-version`
**Purpose:** Increments the version number of a list.

**Parameters:**
- `list_id` (string, path): Unique list identifier

**Returns:** `ListResponse` (updated list with new version)

**Status Codes:**
- 200: Version incremented successfully
- 404: List not found

### GET `/lists/`
**Purpose:** Retrieves all lists with optional pagination and user filtering.

**Parameters:**
- `skip` (int, query, default: 0): Number of records to skip
- `limit` (int, query, default: 100): Maximum records to return
- `user_id` (string, query, optional): Filter by user ID

**Returns:** Array of `ListResponse` objects

**Status Codes:**
- 200: Success

### GET `/lists/{list_id}/stats`
**Purpose:** Provides statistical information about a list (total tasks, completed tasks, etc.).

**Parameters:**
- `list_id` (string, path): Unique list identifier

**Returns:** Statistics object with list metrics

**Status Codes:**
- 200: Success
- 404: List not found

---

## Task Routes (`/tasks`)

### POST `/tasks/`
**Purpose:** Creates a new task within a specific list.

**Parameters:**
- Body: `TaskCreate`
  - `user_id` (string): Task owner's user ID
  - `list_id` (string): Parent list ID
  - `task_name` (string): Task description
  - `reminders` (array of datetime): Reminder timestamps
  - `isPriority` (boolean): Priority flag
  - `isRecurring` (boolean): Recurring task flag
  - `list_version` (int): Target list version

**Returns:** `TaskResponse`
- `user_id` (string): Owner's user ID
- `list_id` (string): Parent list ID
- `task_id` (string): Unique task identifier
- `task_name` (string): Task description
- `reminders` (array of datetime): Reminder timestamps
- `isComplete` (boolean): Completion status
- `isPriority` (boolean): Priority flag
- `isRecurring` (boolean): Recurring task flag
- `createdAt` (datetime): Creation timestamp
- `updatedAt` (datetime): Last update timestamp

**Status Codes:**
- 201: Task created successfully
- 400: Invalid parameters

### GET `/tasks/{task_id}`
**Purpose:** Retrieves a specific task by its ID.

**Parameters:**
- `task_id` (string, path): Unique task identifier

**Returns:** `TaskResponse` (same structure as POST /tasks/)

**Status Codes:**
- 200: Success
- 404: Task not found

### PUT `/tasks/{task_id}`
**Purpose:** Updates an existing task's properties.

**Parameters:**
- `task_id` (string, path): Unique task identifier
- Body: `TaskUpdate`
  - `user_id` (string, optional): New owner ID
  - `list_id` (string, optional): New parent list ID
  - `task_id` (string, optional): New task ID
  - `task_name` (string, optional): New task name
  - `reminders` (array of datetime, optional): New reminders
  - `isComplete` (boolean, optional): Completion status
  - `isPriority` (boolean, optional): Priority flag
  - `isRecurring` (boolean, optional): Recurring flag
  - `createdAt` (datetime, optional): Creation time
  - `updatedAt` (datetime, optional): Update time

**Returns:** `TaskResponse` (updated task data)

**Status Codes:**
- 200: Task updated successfully
- 400: Invalid parameters
- 404: Task not found

### DELETE `/tasks/{task_id}`
**Purpose:** Permanently deletes a task.

**Parameters:**
- `task_id` (string, path): Unique task identifier

**Returns:** Success confirmation

**Status Codes:**
- 200: Task deleted successfully
- 404: Task not found
- 500: Failed to delete task

### PATCH `/tasks/toggle-complete/{task_id}`
**Purpose:** Toggles the completion status of a task.

**Parameters:**
- `task_id` (string, path): Unique task identifier

**Returns:** `TaskResponse` (updated task with toggled completion)

**Status Codes:**
- 200: Completion status toggled successfully
- 400: Unable to toggle completion
- 404: Task not found

### PATCH `/tasks/toggle-recurring/{task_id}`
**Purpose:** Toggles the recurring status of a task.

**Parameters:**
- `task_id` (string, path): Unique task identifier

**Returns:** `TaskResponse` (updated task with toggled recurring status)

**Status Codes:**
- 200: Recurring status toggled successfully
- 400: Unable to toggle recurring status
- 404: Task not found

### PATCH `/tasks/toggle-priority/{task_id}`
**Purpose:** Toggles the priority status of a task.

**Parameters:**
- `task_id` (string, path): Unique task identifier

**Returns:** `TaskResponse` (updated task with toggled priority)

**Status Codes:**
- 200: Priority status toggled successfully
- 400: Unable to toggle priority
- 404: Task not found

### PATCH `/tasks/clear-list/{list_id}`
**Purpose:** Removes all tasks from a specific list.

**Parameters:**
- `list_id` (string, path): List identifier to clear

**Returns:** Array of `TaskResponse` objects (cleared tasks)

**Status Codes:**
- 200: List cleared successfully
- 400: No tasks to remove
- 404: List not found

### POST `/tasks/rollover-list/{list_id}`
**Purpose:** Creates a new list version containing only incomplete tasks from current version.

**Parameters:**
- `list_id` (string, path): Source list identifier

**Returns:** Array of `TaskResponse` objects (rolled over tasks)

**Status Codes:**
- 201: List rolled over successfully
- 400: Invalid version request
- 404: List not found

### GET `/tasks/list/{list_id}/current`
**Purpose:** Retrieves all current tasks from a specific list.

**Parameters:**
- `list_id` (string, path): List identifier

**Returns:** Array of `TaskResponse` objects

**Status Codes:**
- 200: Success
- 404: List not found

### GET `/tasks/list/{list_id}/versions`
**Purpose:** Retrieves tasks from multiple versions of a list with pagination.

**Parameters:**
- `list_id` (string, path): List identifier
- `page_start` (int, query, default: 0): Starting page number
- `page_end` (int, query, default: 10): Ending page number

**Returns:** Array of arrays of `TaskResponse` objects (grouped by version)

**Status Codes:**
- 200: Success
- 400: Invalid version request
- 404: List not found

---

## Error Handling

All endpoints use consistent HTTP status codes:

- **200**: Success
- **201**: Created successfully
- **400**: Bad request (invalid parameters, no fields to update, etc.)
- **401**: Unauthorized (invalid credentials)
- **404**: Resource not found
- **409**: Conflict (resource already exists)
- **500**: Internal server error

Error responses include a `detail` field with a descriptive error message.

## Data Models Summary

### UserCreate
Required fields for creating a user: username, email, password, phone_number, first_name, last_name, google_id

### UserUpdate
Optional fields for updating a user: username, email, phone_number, first_name, last_name, google_id

### UserResponse
Complete user data: user_id, username, email, phone_number, first_name, last_name, created_at, last_updated_at

### ListCreate
Required fields for creating a list: user_id, list_name

### ListUpdate
Optional fields for updating a list: list_id, user_id, list_name, created_at, last_updated_at, version

### ListResponse
Complete list data: list_id, user_id, list_name, created_at, last_updated_at, version

### TaskCreate
Required fields for creating a task: user_id, list_id, task_name, reminders, isPriority, isRecurring, list_version

### TaskUpdate
Optional fields for updating a task: user_id, list_id, task_id, task_name, reminders, isComplete, isPriority, isRecurring, createdAt, updatedAt

### TaskResponse
Complete task data: user_id, list_id, task_id, task_name, reminders, isComplete, isPriority, isRecurring, createdAt, updatedAt