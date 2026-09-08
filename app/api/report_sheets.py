from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models.academic_session import AcademicSession
from app.models.class_model import Class
from app.models.enrollment import Enrollment
from app.models.published_report_snapshot import (
    PublishedReportSnapshot,
)
from app.models.result_publication import ResultPublication
from app.models.user import User
from app.schemas.report_sheet import StudentReportSheetResponse
from app.services.report_sheet_service import (
    build_student_report_sheet,
)


router = APIRouter(
    prefix="/api/report-sheets",
    tags=["Report Sheets"],
)


@router.get(
    "/student/{student_id}",
    response_model=StudentReportSheetResponse,
)
def get_student_report_sheet(
    student_id: int,
    academic_session_id: int,
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.academic_session_id
            == academic_session_id,
        )
    )

    if enrollment is not None:
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
                ResultPublication.class_id
                == enrollment.class_id,
                ResultPublication.academic_session_id
                == academic_session_id,
                ResultPublication.term_id == term_id,
                ResultPublication.status == "published",
                Class.school_id == current_user.school_id,
                AcademicSession.school_id
                == current_user.school_id,
            )
        )

        if publication is not None:
            snapshot = db.scalar(
                select(PublishedReportSnapshot).where(
                    PublishedReportSnapshot.publication_id
                    == publication.id,
                    PublishedReportSnapshot.student_id
                    == student_id,
                )
            )

            if snapshot is not None:
                return StudentReportSheetResponse.model_validate(
                    snapshot.report_data
                )

    return build_student_report_sheet(
        db=db,
        school_id=current_user.school_id,
        student_id=student_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
    )
