from fastapi import FastAPI

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
