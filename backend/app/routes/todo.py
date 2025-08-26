from fastapi import APIRouter
from app.controllers.todo_controller import router as todo_router

router = APIRouter()

router.include_router(todo_router, prefix="/todos", tags=["todos"])
