from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.database.connection import get_db
from app.models import (
    AcademicSession,
    Class,
    Enrollment,
    Student,
    User,
)
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse,
    EnrollmentUpdate,
)

router = APIRouter(
    prefix="/api/enrollments",
    tags=["Enrollments"],
)


@router.post(
    "",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    enrollment_data: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Check student exists
    student = db.scalar(
        select(Student).where(
            Student.id == enrollment_data.student_id
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Check class exists
    class_obj = db.scalar(
        select(Class).where(
            Class.id == enrollment_data.class_id
        )
    )

    if class_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    # Check academic session exists
    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id == enrollment_data.academic_session_id
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    # Check for duplicate enrollment
    existing_enrollment = db.scalar(
        select(Enrollment).where(
            (Enrollment.student_id == enrollment_data.student_id)
            & (Enrollment.class_id == enrollment_data.class_id)
            & (
                Enrollment.academic_session_id
                == enrollment_data.academic_session_id
            )
        )
    )

    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this class for this academic session",
        )

    enrollment = Enrollment(
        student_id=enrollment_data.student_id,
        class_id=enrollment_data.class_id,
        academic_session_id=enrollment_data.academic_session_id,
    )

    db.add(enrollment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this class for this academic session",
        )

    db.refresh(enrollment)

    return enrollment


@router.get(
    "",
    response_model=list[EnrollmentResponse],
)
def get_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    enrollments = db.scalars(
        select(Enrollment).order_by(Enrollment.id)
    ).all()

    return enrollments


@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
)
def get_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.id == enrollment_id
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )

    return enrollment


@router.patch(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
)
def update_enrollment(
    enrollment_id: int,
    enrollment_data: EnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.id == enrollment_id
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )

    update_data = enrollment_data.model_dump(
        exclude_unset=True
    )

    # Determine the values that will exist after the update.
    new_class_id = update_data.get(
        "class_id",
        enrollment.class_id,
    )

    new_academic_session_id = update_data.get(
        "academic_session_id",
        enrollment.academic_session_id,
    )

    # Validate class if it is being changed.
    if "class_id" in update_data:
        class_obj = db.scalar(
            select(Class).where(
                Class.id == new_class_id
            )
        )

        if class_obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found",
            )

    # Validate academic session if it is being changed.
    if "academic_session_id" in update_data:
        academic_session = db.scalar(
            select(AcademicSession).where(
                AcademicSession.id == new_academic_session_id
            )
        )

        if academic_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic session not found",
            )

    # Check whether the update would create a duplicate.
    duplicate = db.scalar(
        select(Enrollment).where(
            (Enrollment.student_id == enrollment.student_id)
            & (Enrollment.class_id == new_class_id)
            & (
                Enrollment.academic_session_id
                == new_academic_session_id
            )
            & (Enrollment.id != enrollment_id)
        )
    )

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Student is already enrolled in this class "
                "for this academic session"
            ),
        )

    if "class_id" in update_data:
        enrollment.class_id = new_class_id

    if "academic_session_id" in update_data:
        enrollment.academic_session_id = new_academic_session_id

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Student is already enrolled in this class "
                "for this academic session"
            ),
        )

    db.refresh(enrollment)

    return enrollment


@router.delete(
    "/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.id == enrollment_id
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )

    db.delete(enrollment)
    db.commit()

    return None
