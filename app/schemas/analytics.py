from pydantic import BaseModel


class SubjectAnalyticsItem(BaseModel):
    subject_id: int
    subject_name: str
    class_average: float | None
    completed_students: int


class ClassAnalyticsResponse(BaseModel):
    class_id: int
    class_name: str

    academic_session_id: int
    term_id: int

    enrolled_students: int
    complete_results: int
    incomplete_results: int

    highest_average: float | None
    lowest_average: float | None
    class_average: float | None

    subjects: list[SubjectAnalyticsItem]