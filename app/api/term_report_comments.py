from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
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
from app.services.subscription_service import (
    require_active_term_subscription,
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
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. VALIDATE STUDENT TENANCY
    # ---------------------------------------------------------

    student = db.scalar(
        select(Student).where(
            Student.id == comment_data.student_id,
            Student.school_id == current_user.school_id,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # ---------------------------------------------------------
    # 2. VALIDATE ACADEMIC SESSION TENANCY
    # ---------------------------------------------------------

    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id
            == comment_data.academic_session_id,
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
    # 3. VALIDATE TERM TENANCY
    # ---------------------------------------------------------

    term = db.scalar(
        select(Term)
        .join(
            AcademicSession,
            Term.academic_session_id == AcademicSession.id,
        )
        .where(
            Term.id == comment_data.term_id,
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
        != comment_data.academic_session_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Term does not belong to the selected "
                "academic session"
            ),
        )

    # ---------------------------------------------------------
    # 4. REQUIRE ACTIVE TERM SUBSCRIPTION
    # ---------------------------------------------------------

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=comment_data.academic_session_id,
        term_id=comment_data.term_id,
    )

    # ---------------------------------------------------------
    # 5. CHECK FOR EXISTING COMMENT
    # ---------------------------------------------------------

    existing_comment = db.scalar(
        select(TermReportComment).where(
            TermReportComment.student_id
            == comment_data.student_id,
            TermReportComment.academic_session_id
            == comment_data.academic_session_id,
            TermReportComment.term_id
            == comment_data.term_id,
        )
    )

    if existing_comment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Report comment already exists for this "
                "student, session and term"
            ),
        )

    # ---------------------------------------------------------
    # 6. CREATE REPORT COMMENT
    # ---------------------------------------------------------

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
            status_code=status.HTTP_409_CONFLICT,
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
    current_user: User = Depends(require_school_admin),
):
    comments = db.scalars(
        select(TermReportComment)
        .join(
            Student,
            TermReportComment.student_id == Student.id,
        )
        .join(
            AcademicSession,
            TermReportComment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Student.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
        .order_by(TermReportComment.id)
    ).all()

    return comments


@router.get(
    "/{comment_id}",
    response_model=TermReportCommentResponse,
)
def get_term_report_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    comment = db.scalar(
        select(TermReportComment)
        .join(
            Student,
            TermReportComment.student_id == Student.id,
        )
        .join(
            AcademicSession,
            TermReportComment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            TermReportComment.id == comment_id,
            Student.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. GET TENANT-SCOPED REPORT COMMENT
    # ---------------------------------------------------------

    comment = db.scalar(
        select(TermReportComment)
        .join(
            Student,
            TermReportComment.student_id == Student.id,
        )
        .join(
            AcademicSession,
            TermReportComment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            TermReportComment.id == comment_id,
            Student.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report comment not found",
        )

    # ---------------------------------------------------------
    # 2. REQUIRE ACTIVE TERM SUBSCRIPTION
    # ---------------------------------------------------------

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=comment.academic_session_id,
        term_id=comment.term_id,
    )

    # ---------------------------------------------------------
    # 3. UPDATE COMMENT FIELDS
    # ---------------------------------------------------------

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
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. GET TENANT-SCOPED REPORT COMMENT
    # ---------------------------------------------------------

    comment = db.scalar(
        select(TermReportComment)
        .join(
            Student,
            TermReportComment.student_id == Student.id,
        )
        .join(
            AcademicSession,
            TermReportComment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            TermReportComment.id == comment_id,
            Student.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report comment not found",
        )

    # ---------------------------------------------------------
    # 2. REQUIRE ACTIVE TERM SUBSCRIPTION
    # ---------------------------------------------------------

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=comment.academic_session_id,
        term_id=comment.term_id,
    )

    # ---------------------------------------------------------
    # 3. DELETE REPORT COMMENT
    # ---------------------------------------------------------

    db.delete(comment)
    db.commit()

    return None
