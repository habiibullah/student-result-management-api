from datetime import date

from pydantic import BaseModel


class ReportSheetSubject(BaseModel):
    subject_id: int
    subject_name: str

    ca1: float | None
    ca2: float | None
    ca3: float | None
    exam: float | None

    total: float | None
    grade: str | None
    status: str


class ReportSheetAttendance(BaseModel):
    school_days: int
    days_present: int
    days_absent: int
    attendance_percentage: float


class ReportSheetComments(BaseModel):
    teacher_comment: str | None
    principal_comment: str | None


class ReportSheetSchool(BaseModel):
    school_id: int
    school_name: str
    email: str | None
    phone: str | None
    address: str | None
    motto: str | None
    logo_url: str | None


class ReportSheetSettings(BaseModel):
    report_title: str

    show_class_position: bool
    show_class_size: bool
    show_attendance: bool
    show_teacher_comment: bool
    show_principal_comment: bool
    show_school_motto: bool
    show_school_logo: bool
    show_grading_remarks: bool

    principal_designation: str


class ReportSheetStudent(BaseModel):
    student_id: int
    admission_number: str
    full_name: str
    gender: str | None
    date_of_birth: date | None


class ReportSheetClass(BaseModel):
    class_id: int
    class_name: str
    class_size: int


class ReportSheetTerm(BaseModel):
    academic_session_id: int
    academic_session_name: str

    term_id: int
    term_name: str

    closing_date: date | None
    next_term_resumption_date: date | None


class ReportSheetPerformanceSummary(BaseModel):
    total_score: float | None
    number_of_subjects: int
    completed_subjects: int

    average: float | None
    overall_grade: str | None

    class_position: int | None

    result_status: str
    performance_remark: str | None


class StudentReportSheetResponse(BaseModel):
    school_info: ReportSheetSchool
    report_settings: ReportSheetSettings | None = None

    student: ReportSheetStudent
    class_info: ReportSheetClass
    term_info: ReportSheetTerm

    subjects: list[ReportSheetSubject]

    performance: ReportSheetPerformanceSummary

    attendance: ReportSheetAttendance | None
    comments: ReportSheetComments | None
