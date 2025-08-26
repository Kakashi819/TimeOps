from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class RepeatType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    scheduled_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    repeat_type: RepeatType = RepeatType.NONE
    repeat_interval: int = 1
    repeat_end_date: Optional[datetime] = None

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[Priority] = None
    scheduled_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    repeat_type: Optional[RepeatType] = None
    repeat_interval: Optional[int] = None
    repeat_end_date: Optional[datetime] = None

class TodoResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    completed: bool
    priority: Priority
    scheduled_at: Optional[datetime]
    due_date: Optional[datetime]
    repeat_type: RepeatType
    repeat_interval: int
    repeat_end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class TodoListResponse(BaseModel):
    todos: list[TodoResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
