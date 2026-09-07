from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_school_admin,
)
from app.database.connection import get_db
from app.models import AcademicSession, TeachingAssignment, User
from app.schemas.academic_session import (
    AcademicSessionCreate,
    AcademicSessionResponse,
    AcademicSessionUpdate,
)

router = APIRouter(
    prefix="/api/academic-sessions",
    tags=["Academic Sessions"],
)


@router.post(
    "",
    response_model=AcademicSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_academic_session(
    session_data: AcademicSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    existing_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.name == session_data.name,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Academic session with this name "
                "already exists in this school"
            ),
        )

    if session_data.is_current:
        current_sessions = db.scalars(
            select(AcademicSession).where(
                AcademicSession.school_id == current_user.school_id,
                AcademicSession.is_current.is_(True),
            )
        ).all()

        for current_session in current_sessions:
            current_session.is_current = False

    academic_session = AcademicSession(
        school_id=current_user.school_id,
        name=session_data.name,
        is_current=session_data.is_current,
    )

    db.add(academic_session)
    db.commit()
    db.refresh(academic_session)

    return academic_session


@router.get(
    "",
    response_model=list[AcademicSessionResponse],
)
def get_academic_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    sessions = db.scalars(
        select(AcademicSession)
        .where(
            AcademicSession.school_id == current_user.school_id
        )
        .order_by(
            AcademicSession.name.desc()
        )
    ).all()

    return sessions


@router.get(
    "/{session_id}",
    response_model=AcademicSessionResponse,
)
def get_academic_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id == session_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    return academic_session


@router.put(
    "/{session_id}",
    response_model=AcademicSessionResponse,
)
def update_academic_session(
    session_id: int,
    session_data: AcademicSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id == session_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    if session_data.name is not None:
        existing_session = db.scalar(
            select(AcademicSession).where(
                AcademicSession.name == session_data.name,
                AcademicSession.school_id == current_user.school_id,
                AcademicSession.id != session_id,
            )
        )

        if existing_session:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Academic session with this name "
                    "already exists in this school"
                ),
            )

        academic_session.name = session_data.name

    if session_data.is_current is True:
        current_sessions = db.scalars(
            select(AcademicSession).where(
                AcademicSession.school_id == current_user.school_id,
                AcademicSession.is_current.is_(True),
                AcademicSession.id != session_id,
            )
        ).all()

        for current_session in current_sessions:
            current_session.is_current = False

        academic_session.is_current = True

    elif session_data.is_current is False:
        academic_session.is_current = False

    db.commit()
    db.refresh(academic_session)

    return academic_session


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_academic_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id == session_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    assignment_count = db.scalar(
        select(func.count(TeachingAssignment.id)).where(
            TeachingAssignment.academic_session_id
            == academic_session.id
        )
    )

    if assignment_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Academic session cannot be deleted because it has "
                "teaching assignments. Delete the assignments first."
            ),
        )

    db.delete(academic_session)
    db.commit()

    return None
