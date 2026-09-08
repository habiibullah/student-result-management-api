from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models.academic_session import AcademicSession
from app.models.assessment import Assessment
from app.models.class_model import Class
from app.models.enrollment import Enrollment
from app.models.result_publication import ResultPublication
from app.models.published_report_snapshot import (
    PublishedReportSnapshot,
)
from app.models.student_score import StudentScore
from app.models.subject import Subject
from app.models.term import Term
from app.models.user import User
from app.schemas.result_publication import (
    ResultPublicationCreate,
    ResultPublicationResponse,
)
from app.services.result_service import (
    compute_student_term_result,
)
from app.services.subscription_service import (
    require_active_term_subscription,
)
from app.services.report_sheet_service import (
    build_student_report_sheet,
)


router = APIRouter(
    prefix="/api/result-publications",
    tags=["Result Publications"],
)


def validate_result_readiness(
    db: Session,
    school_id: int,
    class_id: int,
    academic_session_id: int,
    term_id: int,
) -> None:
    """
    Ensure the class has students and assessments and
    that every enrolled student's term result is complete.
    """

    # ---------------------------------------------------------
    # 1. GET CLASS ENROLLMENTS
    # ---------------------------------------------------------

    enrollments = db.scalars(
        select(Enrollment).where(
            Enrollment.class_id == class_id,
            Enrollment.academic_session_id
            == academic_session_id,
        )
    ).all()

    if not enrollments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot publish results because the class "
                "has no enrolled students for this session"
            ),
        )

    student_ids = [
        enrollment.student_id
        for enrollment in enrollments
    ]

    # ---------------------------------------------------------
    # 2. GET TERM ASSESSMENTS
    # ---------------------------------------------------------

    assessments = db.scalars(
        select(Assessment).where(
            Assessment.class_id == class_id,
            Assessment.academic_session_id
            == academic_session_id,
            Assessment.term_id == term_id,
        )
    ).all()

    if not assessments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot publish results because no "
                "assessments exist for this class and term"
            ),
        )

    assessment_ids = [
        assessment.id
        for assessment in assessments
    ]

    # ---------------------------------------------------------
    # 3. GET SUBJECTS
    # ---------------------------------------------------------

    subject_ids = list(
        {
            assessment.subject_id
            for assessment in assessments
        }
    )

    subjects = db.scalars(
        select(Subject).where(
            Subject.id.in_(subject_ids),
            Subject.school_id == school_id,
        )
    ).all()

    subjects_by_id = {
        subject.id: subject
        for subject in subjects
    }

    if len(subjects_by_id) != len(subject_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "One or more assessment subjects do not "
                "belong to this school"
            ),
        )

    # ---------------------------------------------------------
    # 4. GET ALL SCORES
    # ---------------------------------------------------------

    scores = db.scalars(
        select(StudentScore).where(
            StudentScore.assessment_id.in_(
                assessment_ids
            ),
            StudentScore.student_id.in_(
                student_ids
            ),
        )
    ).all()

    scores_by_key = {
        (
            score.student_id,
            score.assessment_id,
        ): float(score.score)
        for score in scores
    }

    # ---------------------------------------------------------
    # 5. VERIFY EVERY STUDENT RESULT IS COMPLETE
    # ---------------------------------------------------------

    incomplete_students = []

    for enrollment in enrollments:
        computed = compute_student_term_result(
            student_id=enrollment.student_id,
            assessments=assessments,
            subjects_by_id=subjects_by_id,
            scores_by_key=scores_by_key,
        )

        if computed["result_status"] != "COMPLETE":
            incomplete_students.append(
                enrollment.student_id
            )

    if incomplete_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": (
                    "Cannot publish results because some "
                    "student results are incomplete"
                ),
                "incomplete_student_ids": (
                    incomplete_students
                ),
            },
        )


@router.post(
    "",
    response_model=ResultPublicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def publish_results(
    publication_data: ResultPublicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. VALIDATE CLASS TENANCY
    # ---------------------------------------------------------

    class_record = db.scalar(
        select(Class).where(
            Class.id == publication_data.class_id,
            Class.school_id == current_user.school_id,
        )
    )

    if class_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    # ---------------------------------------------------------
    # 2. VALIDATE ACADEMIC SESSION TENANCY
    # ---------------------------------------------------------

    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id
            == publication_data.academic_session_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    # ---------------------------------------------------------
    # 3. VALIDATE TERM
    # ---------------------------------------------------------

    term = db.scalar(
        select(Term)
        .join(
            AcademicSession,
            Term.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Term.id == publication_data.term_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found",
        )

    if (
        term.academic_session_id
        != publication_data.academic_session_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Term does not belong to the selected "
                "academic session"
            ),
        )

    # ---------------------------------------------------------
    # 4. REQUIRE ACTIVE SUBSCRIPTION
    # ---------------------------------------------------------

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=(
            publication_data.academic_session_id
        ),
        term_id=publication_data.term_id,
    )

    # ---------------------------------------------------------
    # 5. CHECK EXISTING PUBLICATION
    # ---------------------------------------------------------

    existing_publication = db.scalar(
        select(ResultPublication).where(
            ResultPublication.class_id
            == publication_data.class_id,
            ResultPublication.academic_session_id
            == publication_data.academic_session_id,
            ResultPublication.term_id
            == publication_data.term_id,
        )
    )

    if (
        existing_publication is not None
        and existing_publication.status == "published"
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Results are already published for this "
                "class, session and term"
            ),
        )

    # ---------------------------------------------------------
    # 6. VALIDATE RESULT READINESS
    # ---------------------------------------------------------

    validate_result_readiness(
        db=db,
        school_id=current_user.school_id,
        class_id=publication_data.class_id,
        academic_session_id=(
            publication_data.academic_session_id
        ),
        term_id=publication_data.term_id,
    )

    # ---------------------------------------------------------
    # 7. CREATE OR UPDATE PUBLICATION
    # ---------------------------------------------------------

    if existing_publication is not None:
        publication = existing_publication

        publication.status = "published"
        publication.published_by_user_id = (
            current_user.id
        )
        publication.published_at = (
            datetime.utcnow()
        )

    else:
        publication = ResultPublication(
            class_id=publication_data.class_id,
            academic_session_id=(
                publication_data.academic_session_id
            ),
            term_id=publication_data.term_id,
            status="published",
            published_by_user_id=current_user.id,
        )

        db.add(publication)

    # Flush so a new publication receives its database ID
    # before snapshots are created.
    db.flush()

    # ---------------------------------------------------------
    # 8. GET ENROLLED STUDENTS
    # ---------------------------------------------------------

    enrollments = db.scalars(
        select(Enrollment).where(
            Enrollment.class_id
            == publication_data.class_id,
            Enrollment.academic_session_id
            == publication_data.academic_session_id,
        )
    ).all()

    # ---------------------------------------------------------
    # 9. CREATE OR UPDATE REPORT SNAPSHOTS
    # ---------------------------------------------------------

    for enrollment in enrollments:
        report = build_student_report_sheet(
            db=db,
            school_id=current_user.school_id,
            student_id=enrollment.student_id,
            academic_session_id=(
                publication_data.academic_session_id
            ),
            term_id=publication_data.term_id,
        )

        report_data = report.model_dump(
            mode="json"
        )

        existing_snapshot = db.scalar(
            select(PublishedReportSnapshot).where(
                PublishedReportSnapshot.publication_id
                == publication.id,
                PublishedReportSnapshot.student_id
                == enrollment.student_id,
            )
        )

        if existing_snapshot is not None:
            existing_snapshot.report_data = (
                report_data
            )
            existing_snapshot.updated_at = (
                datetime.utcnow()
            )

        else:
            snapshot = PublishedReportSnapshot(
                publication_id=publication.id,
                student_id=enrollment.student_id,
                report_data=report_data,
            )

            db.add(snapshot)

    # ---------------------------------------------------------
    # 10. COMMIT PUBLICATION AND SNAPSHOTS TOGETHER
    # ---------------------------------------------------------

    db.commit()
    db.refresh(publication)

    return publication


@router.get(
    "",
    response_model=list[ResultPublicationResponse],
)
def get_result_publications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    publications = db.scalars(
        select(ResultPublication)
        .join(
            Class,
            ResultPublication.class_id == Class.id,
        )
        .join(
            AcademicSession,
            ResultPublication.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Class.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
        .order_by(ResultPublication.id)
    ).all()

    return publications


@router.get(
    "/{publication_id}",
    response_model=ResultPublicationResponse,
)
def get_result_publication(
    publication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    publication = db.scalar(
        select(ResultPublication)
        .join(
            Class,
            ResultPublication.class_id == Class.id,
        )
        .join(
            AcademicSession,
            ResultPublication.academic_session_id
            == AcademicSession.id,
        )
        .where(
            ResultPublication.id == publication_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if publication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result publication not found",
        )

    return publication


@router.patch(
    "/{publication_id}/reopen",
    response_model=ResultPublicationResponse,
)
def reopen_results(
    publication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. GET TENANT-SCOPED PUBLICATION
    # ---------------------------------------------------------

    publication = db.scalar(
        select(ResultPublication)
        .join(
            Class,
            ResultPublication.class_id == Class.id,
        )
        .join(
            AcademicSession,
            ResultPublication.academic_session_id
            == AcademicSession.id,
        )
        .where(
            ResultPublication.id == publication_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if publication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result publication not found",
        )

    if publication.status != "published":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Results are already reopened",
        )

    # ---------------------------------------------------------
    # 2. REQUIRE ACTIVE SUBSCRIPTION
    # ---------------------------------------------------------

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=(
            publication.academic_session_id
        ),
        term_id=publication.term_id,
    )

    # ---------------------------------------------------------
    # 3. REOPEN
    # ---------------------------------------------------------

    publication.status = "reopened"

    db.commit()
    db.refresh(publication)

    return publication
