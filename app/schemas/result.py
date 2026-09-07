from pydantic import BaseModel


class ResultResponse(BaseModel):
    student_id: int
    subject_id: int
    class_id: int
    academic_session_id: int
    term_id: int

    ca1: float | None
    ca2: float | None
    ca3: float | None
    exam: float | None

    total: float | None
    percentage: float | None
    grade: str | None

    status: str
