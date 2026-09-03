from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.core.security import hash_password
from app.database.connection import get_db
from app.models import Enrollment, Student, User
from app.schemas.student import (
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)

router = APIRouter(
    prefix="/api/students",
    tags=["Students"],
)


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing_user = db.scalar(
        select(User).where(User.email == student_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    existing_student = db.scalar(
        select(Student).where(
            Student.admission_number
            == student_data.admission_number
        )
    )

    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this admission number already exists",
        )

    user = User(
        email=student_data.email,
        password_hash=hash_password(student_data.password),
        role="student",
        is_active=True,
    )

    db.add(user)

    try:
        db.flush()

        student = Student(
            user_id=user.id,
            admission_number=student_data.admission_number,
            first_name=student_data.first_name,
            last_name=student_data.last_name,
            date_of_birth=student_data.date_of_birth,
            gender=student_data.gender,
        )

        db.add(student)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student could not be created because of a duplicate record",
        )

    db.refresh(student)

    return student


@router.get(
    "",
    response_model=list[StudentResponse],
)
def get_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    students = db.scalars(
        select(Student).order_by(Student.last_name, Student.first_name)
    ).all()

    return students


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    student = db.scalar(
        select(Student).where(Student.id == student_id)
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return student


@router.patch(
    "/{student_id}",
    response_model=StudentResponse,
)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    student = db.scalar(
        select(Student).where(Student.id == student_id)
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    user = db.scalar(
        select(User).where(User.id == student.user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student user account not found",
        )

    update_data = student_data.model_dump(exclude_unset=True)

    # Check email uniqueness
    if "email" in update_data:
        existing_user = db.scalar(
            select(User).where(
                (User.email == update_data["email"])
                & (User.id != student.user_id)
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        user.email = update_data["email"]

    # Check admission number uniqueness
    if "admission_number" in update_data:
        existing_student = db.scalar(
            select(Student).where(
                (Student.admission_number == update_data["admission_number"])
                & (Student.id != student_id)
            )
        )

        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A student with this admission number already exists",
            )

        student.admission_number = update_data["admission_number"]

    # Update student fields
    student_fields = [
        "first_name",
        "last_name",
        "date_of_birth",
        "gender",
    ]

    for field in student_fields:
        if field in update_data:
            setattr(student, field, update_data[field])

    # Update account status
    if "is_active" in update_data:
        user.is_active = update_data["is_active"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student could not be updated because of a duplicate record",
        )

    db.refresh(student)

    return student


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    student = db.scalar(
        select(Student).where(Student.id == student_id)
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    enrollment_count = db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.student_id == student_id
        )
    )

    if enrollment_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Student cannot be deleted because they have enrollments. "
                "Delete the enrollments first."
            ),
        )

    user = db.scalar(
        select(User).where(User.id == student.user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student user account not found",
        )

    try:
        # Delete the student first because student.user_id is non-nullable.
        db.delete(student)
        db.flush()

        # Then delete the associated user account.
        db.delete(user)

        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student could not be deleted because related records exist",
        )

    return None
