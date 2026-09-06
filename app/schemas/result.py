from pydantic import BaseModel


class ResultResponse(BaseModel):
    student_id: int
    subject_id: int
    class_id: int
    academic_session_id: int
    term_id: int

    ca1: float
    ca2: float
    ca3: float
    exam: float

    total: float
    percentage: float
    grade: str
