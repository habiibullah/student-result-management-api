from fastapi import FastAPI
from sqlalchemy import text

from app.database.connection import engine


app = FastAPI(
    title="Student Result Management API",
    description="Backend API for managing students, classes, subjects, scores, and academic results.",
    version="1.0.0",
)


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
