from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.todo import router as todo_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(todo_router, prefix="/api")
