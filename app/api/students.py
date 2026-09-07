from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
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
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. CHECK EMAIL UNIQUENESS
    # ---------------------------------------------------------

    existing_user = db.scalar(
        select(User).where(
            User.email == student_data.email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # ---------------------------------------------------------
    # 2. CHECK ADMISSION NUMBER WITHIN THIS SCHOOL
    # ---------------------------------------------------------

    existing_student = db.scalar(
        select(Student).where(
            Student.admission_number
            == student_data.admission_number,
            Student.school_id
            == current_user.school_id,
        )
    )

    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A student with this admission number "
                "already exists in this school"
            ),
        )

    # ---------------------------------------------------------
    # 3. CREATE STUDENT USER ACCOUNT
    # ---------------------------------------------------------

    user = User(
        email=student_data.email,
        password_hash=hash_password(
            student_data.password
        ),
        role="student",
        is_active=True,
        school_id=current_user.school_id,
    )

    db.add(user)

    try:
        db.flush()

        # -----------------------------------------------------
        # 4. CREATE STUDENT PROFILE
        # -----------------------------------------------------

        student = Student(
            user_id=user.id,
            school_id=current_user.school_id,
            admission_number=(
                student_data.admission_number
            ),
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
            detail=(
                "Student could not be created because "
                "of a duplicate record"
            ),
        )

    db.refresh(student)

    return student


@router.get(
    "",
    response_model=list[StudentResponse],
)
def get_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # RETURN ONLY STUDENTS FROM CURRENT ADMIN'S SCHOOL
    # ---------------------------------------------------------

    students = db.scalars(
        select(Student)
        .where(
            Student.school_id
            == current_user.school_id
        )
        .order_by(
            Student.last_name,
            Student.first_name,
        )
    ).all()

    return students


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # GET STUDENT ONLY FROM CURRENT SCHOOL
    # ---------------------------------------------------------

    student = db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.school_id
            == current_user.school_id,
        )
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
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. GET STUDENT FROM CURRENT SCHOOL
    # ---------------------------------------------------------

    student = db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.school_id
            == current_user.school_id,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # ---------------------------------------------------------
    # 2. GET ASSOCIATED USER FROM SAME SCHOOL
    # ---------------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.id == student.user_id,
            User.school_id
            == current_user.school_id,
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student user account not found",
        )

    update_data = student_data.model_dump(
        exclude_unset=True
    )

    # ---------------------------------------------------------
    # 3. CHECK EMAIL UNIQUENESS
    # ---------------------------------------------------------

    if "email" in update_data:
        existing_user = db.scalar(
            select(User).where(
                User.email
                == update_data["email"],
                User.id
                != student.user_id,
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A user with this email already exists"
                ),
            )

        user.email = update_data["email"]

    # ---------------------------------------------------------
    # 4. CHECK ADMISSION NUMBER WITHIN SCHOOL
    # ---------------------------------------------------------

    if "admission_number" in update_data:
        existing_student = db.scalar(
            select(Student).where(
                Student.admission_number
                == update_data["admission_number"],
                Student.school_id
                == current_user.school_id,
                Student.id
                != student_id,
            )
        )

        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A student with this admission number "
                    "already exists in this school"
                ),
            )

        student.admission_number = (
            update_data["admission_number"]
        )

    # ---------------------------------------------------------
    # 5. UPDATE STUDENT PROFILE FIELDS
    # ---------------------------------------------------------

    student_fields = [
        "first_name",
        "last_name",
        "date_of_birth",
        "gender",
    ]

    for field in student_fields:
        if field in update_data:
            setattr(
                student,
                field,
                update_data[field],
            )

    # ---------------------------------------------------------
    # 6. UPDATE USER ACCOUNT STATUS
    # ---------------------------------------------------------

    if "is_active" in update_data:
        user.is_active = update_data["is_active"]

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Student could not be updated because "
                "of a duplicate record"
            ),
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
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. GET STUDENT FROM CURRENT SCHOOL
    # ---------------------------------------------------------

    student = db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.school_id
            == current_user.school_id,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # ---------------------------------------------------------
    # 2. CHECK FOR EXISTING ENROLLMENTS
    # ---------------------------------------------------------

    enrollment_count = db.scalar(
        select(
            func.count(Enrollment.id)
        ).where(
            Enrollment.student_id
            == student.id
        )
    )

    if enrollment_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Student cannot be deleted because "
                "they have enrollments. "
                "Delete the enrollments first."
            ),
        )

    # ---------------------------------------------------------
    # 3. GET ASSOCIATED USER FROM CURRENT SCHOOL
    # ---------------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.id == student.user_id,
            User.school_id
            == current_user.school_id,
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student user account not found",
        )

    # ---------------------------------------------------------
    # 4. DELETE STUDENT AND USER
    # ---------------------------------------------------------

    try:
        # Student must be deleted first because
        # student.user_id is non-nullable.
        db.delete(student)
        db.flush()

        db.delete(user)

        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Student could not be deleted because "
                "related records exist"
            ),
        )

    return None
