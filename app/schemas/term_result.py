from pydantic import BaseModel
from datetime import date

class AttendanceSummary(BaseModel):
    school_days: int
    days_present: int
    days_absent: int
    attendance_percentage: float


class ReportCommentSummary(BaseModel):
    teacher_comment: str | None
    principal_comment: str | None


class SubjectResultSummary(BaseModel):
    subject_id: int
    subject_name: str

    ca1: float | None
    ca2: float | None
    ca3: float | None
    exam: float | None

    total: float | None
    grade: str | None
    status: str


class StudentTermResultResponse(BaseModel):
    student_id: int
    admission_number: str
    student_name: str

    class_id: int
    academic_session_id: int
    term_id: int

    subjects: list[SubjectResultSummary]

    total_score: float | None
    number_of_subjects: int
    completed_subjects: int

    average: float | None
    overall_grade: str | None

    result_status: str
    class_position: int | None
    class_size: int

    remark: str | None

    attendance: AttendanceSummary | None
    comments: ReportCommentSummary | None
    closing_date: date | None
    next_term_resumption_date: date | None
