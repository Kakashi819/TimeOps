# TimeOps Backend

A FastAPI-based backend with Google OAuth authentication and comprehensive todo management system.

## Features

### Authentication

- Google OAuth signup/signin
- Session-based authentication
- User management

### Todo Management

- Create, read, update, delete todos
- Priority levels (low, medium, high, urgent)
- Scheduling todos for specific dates/times
- Due date tracking
- Repeating todos (daily, weekly, monthly, yearly)
- Completion tracking
- Overdue todo detection
- Upcoming todo queries

## API Endpoints

### Authentication

- `GET /auth/signup` - Initiate Google OAuth signup
- `GET /auth/signin` - Initiate Google OAuth signin
- `GET /auth/callback` - Handle OAuth callback
- `GET /auth/user` - Get current user info
- `POST /auth/logout` - Logout user

### Todos

- `POST /api/todos/` - Create a new todo
- `GET /api/todos/` - Get todos with filtering and pagination
- `GET /api/todos/{todo_id}` - Get specific todo
- `PUT /api/todos/{todo_id}` - Update todo
- `DELETE /api/todos/{todo_id}` - Delete todo
- `GET /api/todos/scheduled/{date}` - Get todos for specific date
- `GET /api/todos/overdue/list` - Get overdue todos
- `GET /api/todos/upcoming/list` - Get upcoming todos
- `GET /api/todos/repeating/list` - Get repeating todos
- `POST /api/todos/{todo_id}/complete` - Mark todo as completed
- `POST /api/todos/{todo_id}/incomplete` - Mark todo as incomplete

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Setup PostgreSQL database and update `.env`:

   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/timeops_db
   ```

3. Run the server:
   ```bash
   python main.py
   ```

## Authentication Usage

For authenticated endpoints, include the session ID in the Authorization header:

```
Authorization: Bearer <session_id>
```

## Todo Features

### Scheduling

- Set `scheduled_at` for when the todo should be done
- Set `due_date` for deadline

### Repeating Todos

- Set `repeat_type`: none, daily, weekly, monthly, yearly
- Set `repeat_interval`: every X days/weeks/months
- Set `repeat_end_date`: when to stop repeating

### Priority Levels

- `low` - Low priority
- `medium` - Medium priority (default)
- `high` - High priority
- `urgent` - Urgent priority

The system automatically generates future occurrences for repeating todos.
