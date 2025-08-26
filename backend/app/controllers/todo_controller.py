from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date
from app.database import get_db, User
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse, TodoListResponse
from app.services.todo_service import TodoService

router = APIRouter()

# Temporary: Get first user for testing (remove when auth is re-enabled)
def get_test_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No users found. Please sign up first.")
    return user

@router.post("/", response_model=TodoResponse)
def create_todo(
    todo_data: TodoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Create a new todo"""
    todo_service = TodoService(db)
    todo = todo_service.create_todo(current_user, todo_data)
    return todo

@router.get("/", response_model=TodoListResponse)
def get_todos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    completed: Optional[bool] = Query(None),
    priority: Optional[str] = Query(None),
    scheduled_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Get todos with filtering and pagination"""
    todo_service = TodoService(db)
    
    # Convert date to datetime if provided
    scheduled_datetime = None
    if scheduled_date:
        scheduled_datetime = datetime.combine(scheduled_date, datetime.min.time())
    
    todos, total = todo_service.get_todos(
        current_user, 
        skip=skip, 
        limit=limit,
        completed=completed,
        priority=priority,
        scheduled_date=scheduled_datetime
    )
    
    # Calculate pagination info
    page = (skip // limit) + 1
    has_next = (skip + limit) < total
    has_prev = skip > 0
    
    return TodoListResponse(
        todos=todos,
        total=total,
        page=page,
        page_size=limit,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Get a specific todo by ID"""
    todo_service = TodoService(db)
    todo = todo_service.get_todo_by_id(current_user, todo_id)
    
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return todo

@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Update a todo"""
    todo_service = TodoService(db)
    todo = todo_service.update_todo(current_user, todo_id, todo_data)
    
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return todo

@router.delete("/{todo_id}")
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Delete a todo"""
    todo_service = TodoService(db)
    success = todo_service.delete_todo(current_user, todo_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return JSONResponse({"message": "Todo deleted successfully"})

@router.get("/scheduled/{date}", response_model=List[TodoResponse])
def get_scheduled_todos(
    date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Get todos scheduled for a specific date"""
    todo_service = TodoService(db)
    scheduled_datetime = datetime.combine(date, datetime.min.time())
    todos = todo_service.get_scheduled_todos(current_user, scheduled_datetime)
    return todos

@router.get("/overdue/list", response_model=List[TodoResponse])
def get_overdue_todos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Get all overdue todos"""
    todo_service = TodoService(db)
    todos = todo_service.get_overdue_todos(current_user)
    return todos

@router.get("/upcoming/list", response_model=List[TodoResponse])
def get_upcoming_todos(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Get upcoming todos in the next X days"""
    todo_service = TodoService(db)
    todos = todo_service.get_upcoming_todos(current_user, days)
    return todos

@router.get("/repeating/list", response_model=List[TodoResponse])
def get_repeating_todos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Get all repeating todos (master templates)"""
    todo_service = TodoService(db)
    todos = todo_service.get_repeating_todos(current_user)
    return todos

@router.post("/{todo_id}/complete", response_model=TodoResponse)
def mark_todo_completed(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Mark a todo as completed"""
    todo_service = TodoService(db)
    todo = todo_service.mark_completed(current_user, todo_id)
    
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return todo

@router.post("/{todo_id}/incomplete", response_model=TodoResponse)
def mark_todo_incomplete(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_test_user)
):
    """Mark a todo as incomplete"""
    todo_service = TodoService(db)
    todo = todo_service.mark_incomplete(current_user, todo_id)
    
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return todo
