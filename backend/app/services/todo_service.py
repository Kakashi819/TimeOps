from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
from app.database import Todo, User
from app.schemas.todo import TodoCreate, TodoUpdate
from app.utils.todo_utils import generate_repeating_todos, is_overdue

class TodoService:
    def __init__(self, db: Session):
        self.db = db

    def create_todo(self, user: User, todo_data: TodoCreate) -> Todo:
        """Create a new todo"""
        todo = Todo(
            user_id=user.id,
            title=todo_data.title,
            description=todo_data.description,
            priority=todo_data.priority,
            scheduled_at=todo_data.scheduled_at,
            due_date=todo_data.due_date,
            repeat_type=todo_data.repeat_type,
            repeat_interval=todo_data.repeat_interval,
            repeat_end_date=todo_data.repeat_end_date
        )
        
        self.db.add(todo)
        self.db.commit()
        self.db.refresh(todo)
        
        # Generate repeating todos if needed
        if todo.repeat_type.value != "none":
            self._generate_future_occurrences(todo)
        
        return todo

    def get_todo_by_id(self, user: User, todo_id: int) -> Optional[Todo]:
        """Get a todo by ID for a specific user"""
        return self.db.query(Todo).filter(
            and_(Todo.id == todo_id, Todo.user_id == user.id)
        ).first()

    def get_todos(
        self, 
        user: User, 
        skip: int = 0, 
        limit: int = 100,
        completed: Optional[bool] = None,
        priority: Optional[str] = None,
        scheduled_date: Optional[datetime] = None
    ) -> tuple[List[Todo], int]:
        """Get todos with filtering and pagination"""
        query = self.db.query(Todo).filter(Todo.user_id == user.id)
        
        # Apply filters
        if completed is not None:
            query = query.filter(Todo.completed == completed)
        
        if priority:
            query = query.filter(Todo.priority == priority)
        
        if scheduled_date:
            start_of_day = scheduled_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            query = query.filter(Todo.scheduled_at.between(start_of_day, end_of_day))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        todos = query.order_by(desc(Todo.created_at)).offset(skip).limit(limit).all()
        
        return todos, total

    def update_todo(self, user: User, todo_id: int, todo_data: TodoUpdate) -> Optional[Todo]:
        """Update a todo"""
        todo = self.get_todo_by_id(user, todo_id)
        if not todo:
            return None
        
        # Update fields
        update_data = todo_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(todo, field, value)
        
        # Set completion timestamp
        if todo_data.completed is not None:
            if todo_data.completed and not todo.completed_at:
                todo.completed_at = datetime.utcnow()
            elif not todo_data.completed:
                todo.completed_at = None
        
        self.db.commit()
        self.db.refresh(todo)
        
        return todo

    def delete_todo(self, user: User, todo_id: int) -> bool:
        """Delete a todo"""
        todo = self.get_todo_by_id(user, todo_id)
        if not todo:
            return False
        
        self.db.delete(todo)
        self.db.commit()
        return True

    def get_scheduled_todos(self, user: User, date: datetime) -> List[Todo]:
        """Get todos scheduled for a specific date"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        return self.db.query(Todo).filter(
            and_(
                Todo.user_id == user.id,
                Todo.scheduled_at.between(start_of_day, end_of_day)
            )
        ).order_by(Todo.scheduled_at).all()

    def get_overdue_todos(self, user: User) -> List[Todo]:
        """Get all overdue todos"""
        current_time = datetime.utcnow()
        return self.db.query(Todo).filter(
            and_(
                Todo.user_id == user.id,
                Todo.completed == False,
                Todo.due_date < current_time
            )
        ).order_by(Todo.due_date).all()

    def get_upcoming_todos(self, user: User, days: int = 7) -> List[Todo]:
        """Get upcoming todos in the next X days"""
        current_time = datetime.utcnow()
        end_time = current_time + timedelta(days=days)
        
        return self.db.query(Todo).filter(
            and_(
                Todo.user_id == user.id,
                Todo.completed == False,
                Todo.scheduled_at.between(current_time, end_time)
            )
        ).order_by(Todo.scheduled_at).all()

    def get_repeating_todos(self, user: User) -> List[Todo]:
        """Get all repeating todos (master templates)"""
        return self.db.query(Todo).filter(
            and_(
                Todo.user_id == user.id,
                Todo.repeat_type != "none"
            )
        ).order_by(desc(Todo.created_at)).all()

    def _generate_future_occurrences(self, todo: Todo, days_ahead: int = 30):
        """Generate future occurrences for a repeating todo"""
        generated_todos = generate_repeating_todos(self.db, todo.user_id, days_ahead)
        
        for generated_todo in generated_todos:
            self.db.add(generated_todo)
        
        if generated_todos:
            self.db.commit()

    def mark_completed(self, user: User, todo_id: int) -> Optional[Todo]:
        """Mark a todo as completed"""
        todo = self.get_todo_by_id(user, todo_id)
        if not todo:
            return None
        
        todo.completed = True
        todo.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(todo)
        
        return todo

    def mark_incomplete(self, user: User, todo_id: int) -> Optional[Todo]:
        """Mark a todo as incomplete"""
        todo = self.get_todo_by_id(user, todo_id)
        if not todo:
            return None
        
        todo.completed = False
        todo.completed_at = None
        
        self.db.commit()
        self.db.refresh(todo)
        
        return todo
