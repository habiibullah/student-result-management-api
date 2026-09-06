from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.database.connection import get_db
from app.models.academic_session import AcademicSession
from app.models.student import Student
from app.models.term import Term
from app.models.term_report_comment import TermReportComment
from app.models.user import User
from app.schemas.term_report_comment import (
    TermReportCommentCreate,
    TermReportCommentResponse,
    TermReportCommentUpdate,
)


router = APIRouter(
    prefix="/api/term-report-comments",
    tags=["Term Report Comments"],
)


@router.post(
    "",
    response_model=TermReportCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_term_report_comment(
    comment_data: TermReportCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    student = db.scalar(
        select(Student).where(
            Student.id == comment_data.student_id
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
            == comment_data.academic_session_id
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=404,
            detail="Academic session not found",
        )

    term = db.scalar(
        select(Term).where(
            Term.id == comment_data.term_id
        )
    )

    if term is None:
        raise HTTPException(
            status_code=404,
            detail="Term not found",
        )

    if (
        term.academic_session_id
        != comment_data.academic_session_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Term does not belong to the selected "
                "academic session"
            ),
        )

    existing_comment = db.scalar(
        select(TermReportComment).where(
            (
                TermReportComment.student_id
                == comment_data.student_id
            )
            & (
                TermReportComment.academic_session_id
                == comment_data.academic_session_id
            )
            & (
                TermReportComment.term_id
                == comment_data.term_id
            )
        )
    )

    if existing_comment:
        raise HTTPException(
            status_code=409,
            detail=(
                "Report comment already exists for this "
                "student, session and term"
            ),
        )

    report_comment = TermReportComment(
        student_id=comment_data.student_id,
        academic_session_id=(
            comment_data.academic_session_id
        ),
        term_id=comment_data.term_id,
        teacher_comment=comment_data.teacher_comment,
        principal_comment=comment_data.principal_comment,
    )

    db.add(report_comment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Report comment already exists",
        )

    db.refresh(report_comment)

    return report_comment


@router.get(
    "",
    response_model=list[TermReportCommentResponse],
)
def get_term_report_comments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return db.scalars(
        select(TermReportComment).order_by(
            TermReportComment.id
        )
    ).all()


@router.get(
    "/{comment_id}",
    response_model=TermReportCommentResponse,
)
def get_term_report_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    comment = db.scalar(
        select(TermReportComment).where(
            TermReportComment.id == comment_id
        )
    )

    if comment is None:
        raise HTTPException(
            status_code=404,
            detail="Report comment not found",
        )

    return comment


@router.patch(
    "/{comment_id}",
    response_model=TermReportCommentResponse,
)
def update_term_report_comment(
    comment_id: int,
    comment_data: TermReportCommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    comment = db.scalar(
        select(TermReportComment).where(
            TermReportComment.id == comment_id
        )
    )

    if comment is None:
        raise HTTPException(
            status_code=404,
            detail="Report comment not found",
        )

    update_data = comment_data.model_dump(
        exclude_unset=True
    )

    if "teacher_comment" in update_data:
        comment.teacher_comment = update_data[
            "teacher_comment"
        ]

    if "principal_comment" in update_data:
        comment.principal_comment = update_data[
            "principal_comment"
        ]

    db.commit()
    db.refresh(comment)

    return comment


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_term_report_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    comment = db.scalar(
        select(TermReportComment).where(
            TermReportComment.id == comment_id
        )
    )

    if comment is None:
        raise HTTPException(
            status_code=404,
            detail="Report comment not found",
        )

    db.delete(comment)
    db.commit()

    return None
