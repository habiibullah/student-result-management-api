from fastapi import FastAPI
from sqlalchemy import text


from app.api.roles import router as roles_router
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.database.connection import engine
from app.api.subjects import router as subjects_router
from app.api.teachers import router as teachers_router
from app.api.teaching_assignments import router as teaching_assignments_router
from app.api.classes import router as classes_router
from app.api.academic_sessions import router as academic_sessions_router

app = FastAPI(
    title="Student Result Management API",
    description="Backend API for managing students, classes, subjects, scores, and academic results.",
    version="1.0.0",
)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(subjects_router)
app.include_router(teachers_router)
app.include_router(teaching_assignments_router)
app.include_router(classes_router)
app.include_router(academic_sessions_router)

@app.get("/")
def root():
    return {
        "message": "Student Result Management API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/health/database")
def database_health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "connected"
    }
