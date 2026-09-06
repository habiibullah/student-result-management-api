from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.database.connection import get_db
from app.models.academic_session import AcademicSession
from app.models.student import Student
from app.models.student_attendance import StudentAttendance
from app.models.term import Term
from app.models.user import User
from app.schemas.student_attendance import (
    StudentAttendanceCreate,
    StudentAttendanceResponse,
    StudentAttendanceUpdate,
)


router = APIRouter(
    prefix="/api/student-attendance",
    tags=["Student Attendance"],
)


def validate_attendance_values(
    school_days: int,
    days_present: int,
    days_absent: int,
):
    if days_present > school_days:
        raise HTTPException(
            status_code=400,
            detail="Days present cannot exceed school days",
        )

    if days_absent > school_days:
        raise HTTPException(
            status_code=400,
            detail="Days absent cannot exceed school days",
        )

    if days_present + days_absent != school_days:
        raise HTTPException(
            status_code=400,
            detail=(
                "Days present plus days absent "
                "must equal school days"
            ),
        )


@router.post(
    "",
    response_model=StudentAttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student_attendance(
    attendance_data: StudentAttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    student = db.scalar(
        select(Student).where(
            Student.id == attendance_data.student_id
        )
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id
            == attendance_data.academic_session_id
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=404,
            detail="Academic session not found",
        )

    term = db.scalar(
        select(Term).where(
            Term.id == attendance_data.term_id
        )
    )

    if term is None:
        raise HTTPException(
            status_code=404,
            detail="Term not found",
        )

    if (
        term.academic_session_id
        != attendance_data.academic_session_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Term does not belong to the selected "
                "academic session"
            ),
        )

    existing_attendance = db.scalar(
        select(StudentAttendance).where(
            (
                StudentAttendance.student_id
                == attendance_data.student_id
            )
            & (
                StudentAttendance.academic_session_id
                == attendance_data.academic_session_id
            )
            & (
                StudentAttendance.term_id
                == attendance_data.term_id
            )
        )
    )

    if existing_attendance:
        raise HTTPException(
            status_code=409,
            detail=(
                "Attendance already exists for this "
                "student, session and term"
            ),
        )

    validate_attendance_values(
        attendance_data.school_days,
        attendance_data.days_present,
        attendance_data.days_absent,
    )

    attendance = StudentAttendance(
        student_id=attendance_data.student_id,
        academic_session_id=(
            attendance_data.academic_session_id
        ),
        term_id=attendance_data.term_id,
        school_days=attendance_data.school_days,
        days_present=attendance_data.days_present,
        days_absent=attendance_data.days_absent,
    )

    db.add(attendance)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Attendance already exists for this "
                "student, session and term"
            ),
        )

    db.refresh(attendance)

    return attendance


@router.get(
    "",
    response_model=list[StudentAttendanceResponse],
)
def get_student_attendance_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    attendance_records = db.scalars(
        select(StudentAttendance).order_by(
            StudentAttendance.id
        )
    ).all()

    return attendance_records


@router.get(
    "/{attendance_id}",
    response_model=StudentAttendanceResponse,
)
def get_student_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    attendance = db.scalar(
        select(StudentAttendance).where(
            StudentAttendance.id == attendance_id
        )
    )

    if attendance is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found",
        )

    return attendance


@router.patch(
    "/{attendance_id}",
    response_model=StudentAttendanceResponse,
)
def update_student_attendance(
    attendance_id: int,
    attendance_data: StudentAttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    attendance = db.scalar(
        select(StudentAttendance).where(
            StudentAttendance.id == attendance_id
        )
    )

    if attendance is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found",
        )

    update_data = attendance_data.model_dump(
        exclude_unset=True
    )

    school_days = update_data.get(
        "school_days",
        attendance.school_days,
    )

    days_present = update_data.get(
        "days_present",
        attendance.days_present,
    )

    days_absent = update_data.get(
        "days_absent",
        attendance.days_absent,
    )

    validate_attendance_values(
        school_days,
        days_present,
        days_absent,
    )

    attendance.school_days = school_days
    attendance.days_present = days_present
    attendance.days_absent = days_absent

    db.commit()
    db.refresh(attendance)

    return attendance


@router.delete(
    "/{attendance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    attendance = db.scalar(
        select(StudentAttendance).where(
            StudentAttendance.id == attendance_id
        )
    )

    if attendance is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found",
        )

    db.delete(attendance)
    db.commit()

    return None
