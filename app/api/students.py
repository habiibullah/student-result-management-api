from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models import Enrollment, Student, User
from app.schemas.student import (
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)

from pathlib import Path
from uuid import uuid4

from fastapi import File, UploadFile
from fastapi.responses import FileResponse
from app.core.student_photo_storage import (
    MAX_PHOTO_BYTES,
    student_photo_directory,
    validate_student_photo,
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
    # 1. CHECK ADMISSION NUMBER WITHIN THIS SCHOOL
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
    # 2. CREATE STUDENT PROFILE
    # ---------------------------------------------------------

    student = Student(
        user_id=None,
        school_id=current_user.school_id,
        admission_number=student_data.admission_number,
        first_name=student_data.first_name,
        last_name=student_data.last_name,
        date_of_birth=student_data.date_of_birth,
        gender=student_data.gender,
    )

    db.add(student)

    try:
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

@router.post(
    "/{student_id}/photo",
    response_model=StudentResponse,
)
def upload_student_photo(
    student_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    student = db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.school_id == current_user.school_id,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    try:
        content = photo.file.read(MAX_PHOTO_BYTES + 1)
        normalized_photo = validate_student_photo(content)
    finally:
        photo.file.close()

    photo_directory = student_photo_directory()
    photo_directory.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}.jpg"
    new_photo_path = photo_directory / filename

    try:
        new_photo_path.write_bytes(normalized_photo)
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save student photograph",
        )

    old_photo_path = student.profile_photo_path
    student.profile_photo_path = filename

    try:
        db.commit()
        db.refresh(student)
    except Exception:
        db.rollback()
        new_photo_path.unlink(missing_ok=True)
        raise

    if old_photo_path and old_photo_path != filename:
        old_path = photo_directory / Path(old_photo_path).name
        old_path.unlink(missing_ok=True)

    return student

@router.get(
    "/{student_id}/photo",
)
def get_student_photo(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    student = db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.school_id == current_user.school_id,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    if not student.profile_photo_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student photograph not found",
        )

    photo_directory = student_photo_directory()
    photo_path = photo_directory / Path(
        student.profile_photo_path
    ).name

    if not photo_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student photograph not found",
        )

    return FileResponse(
        path=photo_path,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )

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

    update_data = student_data.model_dump(
        exclude_unset=True
    )

    # ---------------------------------------------------------
    # 2. CHECK ADMISSION NUMBER WITHIN SCHOOL
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
    # 3. UPDATE STUDENT PROFILE FIELDS
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
    # 3. DELETE STUDENT
    # ---------------------------------------------------------

    try:
        db.delete(student)
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
