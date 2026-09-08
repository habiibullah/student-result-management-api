from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment
from app.models.result_publication import ResultPublication


def require_result_unpublished(
    db: Session,
    class_id: int,
    academic_session_id: int,
    term_id: int,
) -> None:
    publication = db.scalar(
        select(ResultPublication).where(
            ResultPublication.class_id == class_id,
            ResultPublication.academic_session_id
            == academic_session_id,
            ResultPublication.term_id == term_id,
            ResultPublication.status == "published",
        )
    )

    if publication is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Results for this class and term are "
                "published and cannot be modified. "
                "Reopen the results first."
            ),
        )


def require_student_result_unpublished(
    db: Session,
    student_id: int,
    academic_session_id: int,
    term_id: int,
) -> None:
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.academic_session_id
            == academic_session_id,
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Student enrollment not found for the "
                "selected academic session"
            ),
        )

    require_result_unpublished(
        db=db,
        class_id=enrollment.class_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
    )


def require_class_session_results_unpublished(
    db: Session,
    class_id: int,
    academic_session_id: int,
) -> None:
    publication = db.scalar(
        select(ResultPublication).where(
            ResultPublication.class_id == class_id,
            ResultPublication.academic_session_id
            == academic_session_id,
            ResultPublication.status == "published",
        )
    )

    if publication is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Published results exist for this class "
                "and academic session. Enrollment records "
                "cannot be modified until the published "
                "results are reopened."
            ),
        )
