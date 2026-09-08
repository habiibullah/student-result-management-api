from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
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
from app.services.result_publication_service import (
    require_class_session_results_unpublished,
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
    current_user: User = Depends(require_school_admin),
):
    student = db.scalar(
        select(Student).where(
            Student.id == enrollment_data.student_id,
            Student.school_id == current_user.school_id,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    class_obj = db.scalar(
        select(Class).where(
            Class.id == enrollment_data.class_id,
            Class.school_id == current_user.school_id,
        )
    )

    if class_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id
            == enrollment_data.academic_session_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    require_class_session_results_unpublished(
        db=db,
        class_id=enrollment_data.class_id,
        academic_session_id=enrollment_data.academic_session_id,
    )

    existing_enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == enrollment_data.student_id,
            Enrollment.class_id == enrollment_data.class_id,
            Enrollment.academic_session_id
            == enrollment_data.academic_session_id,
        )
    )

    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Student is already enrolled in this class "
                "for this academic session"
            ),
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
            detail=(
                "Student is already enrolled in this class "
                "for this academic session"
            ),
        )

    db.refresh(enrollment)

    return enrollment


@router.get(
    "",
    response_model=list[EnrollmentResponse],
)
def get_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    enrollments = db.scalars(
        select(Enrollment)
        .join(
            Student,
            Enrollment.student_id == Student.id,
        )
        .join(
            Class,
            Enrollment.class_id == Class.id,
        )
        .join(
            AcademicSession,
            Enrollment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Student.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
        .order_by(Enrollment.id)
    ).all()

    return enrollments


@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
)
def get_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    enrollment = db.scalar(
        select(Enrollment)
        .join(
            Student,
            Enrollment.student_id == Student.id,
        )
        .join(
            Class,
            Enrollment.class_id == Class.id,
        )
        .join(
            AcademicSession,
            Enrollment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Enrollment.id == enrollment_id,
            Student.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
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
    current_user: User = Depends(require_school_admin),
):
    enrollment = db.scalar(
        select(Enrollment)
        .join(
            Student,
            Enrollment.student_id == Student.id,
        )
        .join(
            Class,
            Enrollment.class_id == Class.id,
        )
        .join(
            AcademicSession,
            Enrollment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Enrollment.id == enrollment_id,
            Student.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )

    require_class_session_results_unpublished(
        db=db,
        class_id=enrollment.class_id,
        academic_session_id=enrollment.academic_session_id,
    )

    update_data = enrollment_data.model_dump(
        exclude_unset=True
    )

    new_class_id = update_data.get(
        "class_id",
        enrollment.class_id,
    )

    new_academic_session_id = update_data.get(
        "academic_session_id",
        enrollment.academic_session_id,
    )

    if "class_id" in update_data:
        class_obj = db.scalar(
            select(Class).where(
                Class.id == new_class_id,
                Class.school_id == current_user.school_id,
            )
        )

        if class_obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found",
            )

    if "academic_session_id" in update_data:
        academic_session = db.scalar(
            select(AcademicSession).where(
                AcademicSession.id == new_academic_session_id,
                AcademicSession.school_id
                == current_user.school_id,
            )
        )

        if academic_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Academic session not found",
            )

    if (
       new_class_id != enrollment.class_id
       or new_academic_session_id
       != enrollment.academic_session_id
    ):
        require_class_session_results_unpublished(
            db=db,
            class_id=new_class_id,
            academic_session_id=new_academic_session_id,
        )

    duplicate = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == enrollment.student_id,
            Enrollment.class_id == new_class_id,
            Enrollment.academic_session_id
            == new_academic_session_id,
            Enrollment.id != enrollment_id,
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
        enrollment.academic_session_id = (
            new_academic_session_id
        )

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
    current_user: User = Depends(require_school_admin),
):
    enrollment = db.scalar(
        select(Enrollment)
        .join(
            Student,
            Enrollment.student_id == Student.id,
        )
        .join(
            Class,
            Enrollment.class_id == Class.id,
        )
        .join(
            AcademicSession,
            Enrollment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Enrollment.id == enrollment_id,
            Student.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )

    require_class_session_results_unpublished(
        db=db,
        class_id=enrollment.class_id,
        academic_session_id=enrollment.academic_session_id,
    )

    db.delete(enrollment)
    db.commit()

    return None
