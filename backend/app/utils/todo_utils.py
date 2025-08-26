from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database import Todo, RepeatType
from app.schemas.todo import TodoCreate, TodoUpdate

def calculate_next_occurrence(scheduled_at: datetime, repeat_type: RepeatType, repeat_interval: int) -> datetime:
    """Calculate the next occurrence of a repeating todo"""
    if repeat_type == RepeatType.DAILY:
        return scheduled_at + timedelta(days=repeat_interval)
    elif repeat_type == RepeatType.WEEKLY:
        return scheduled_at + timedelta(weeks=repeat_interval)
    elif repeat_type == RepeatType.MONTHLY:
        # Approximate monthly calculation
        return scheduled_at + timedelta(days=30 * repeat_interval)
    elif repeat_type == RepeatType.YEARLY:
        # Approximate yearly calculation
        return scheduled_at + timedelta(days=365 * repeat_interval)
    else:
        return scheduled_at

def should_create_next_occurrence(todo: Todo, current_time: datetime) -> bool:
    """Check if we should create the next occurrence of a repeating todo"""
    if todo.repeat_type == RepeatType.NONE:
        return False
    
    if not todo.scheduled_at:
        return False
    
    # Check if repeat end date has passed
    if todo.repeat_end_date and current_time > todo.repeat_end_date:
        return False
    
    # Check if it's time for next occurrence
    next_occurrence = calculate_next_occurrence(todo.scheduled_at, todo.repeat_type, todo.repeat_interval)
    return current_time >= next_occurrence

def generate_repeating_todos(db: Session, user_id: int, days_ahead: int = 30) -> List[Todo]:
    """Generate repeating todos for the specified number of days ahead"""
    current_time = datetime.utcnow()
    end_time = current_time + timedelta(days=days_ahead)
    
    # Get all repeating todos for the user
    repeating_todos = db.query(Todo).filter(
        and_(
            Todo.user_id == user_id,
            Todo.repeat_type != RepeatType.NONE,
            or_(
                Todo.repeat_end_date.is_(None),
                Todo.repeat_end_date > current_time
            )
        )
    ).all()
    
    generated_todos = []
    
    for todo in repeating_todos:
        if not todo.scheduled_at:
            continue
            
        next_occurrence = calculate_next_occurrence(todo.scheduled_at, todo.repeat_type, todo.repeat_interval)
        
        # Generate occurrences within the time window
        while next_occurrence <= end_time:
            # Check if repeat end date has passed
            if todo.repeat_end_date and next_occurrence > todo.repeat_end_date:
                break
                
            # Check if this occurrence already exists
            existing = db.query(Todo).filter(
                and_(
                    Todo.user_id == user_id,
                    Todo.title == todo.title,
                    Todo.scheduled_at == next_occurrence
                )
            ).first()
            
            if not existing:
                new_todo = Todo(
                    user_id=todo.user_id,
                    title=todo.title,
                    description=todo.description,
                    priority=todo.priority,
                    scheduled_at=next_occurrence,
                    due_date=calculate_next_occurrence(todo.due_date, todo.repeat_type, todo.repeat_interval) if todo.due_date else None,
                    repeat_type=RepeatType.NONE,  # Individual occurrences don't repeat
                    repeat_interval=1,
                    repeat_end_date=None
                )
                generated_todos.append(new_todo)
            
            # Calculate next occurrence
            next_occurrence = calculate_next_occurrence(next_occurrence, todo.repeat_type, todo.repeat_interval)
    
    return generated_todos

def is_overdue(todo: Todo) -> bool:
    """Check if a todo is overdue"""
    if not todo.due_date or todo.completed:
        return False
    return datetime.utcnow() > todo.due_date

def get_upcoming_todos(db: Session, user_id: int, days: int = 7) -> List[Todo]:
    """Get todos that are upcoming in the next X days"""
    current_time = datetime.utcnow()
    end_time = current_time + timedelta(days=days)
    
    return db.query(Todo).filter(
        and_(
            Todo.user_id == user_id,
            Todo.completed == False,
            Todo.scheduled_at.between(current_time, end_time)
        )
    ).order_by(Todo.scheduled_at).all()
