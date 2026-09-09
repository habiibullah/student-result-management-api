from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_school_admin,
)
from app.database.connection import get_db
from app.models.grading_scale import GradingScale
from app.models.user import User
from app.schemas.grading_scale import (
    GradingScaleCreate,
    GradingScaleResponse,
    GradingScaleUpdate,
)


router = APIRouter(
    prefix="/api/grading-scales",
    tags=["Grading Scales"],
)


def find_overlapping_scale(
    db: Session,
    school_id: int,
    minimum_score: float,
    maximum_score: float,
    exclude_id: int | None = None,
):
    query = select(GradingScale).where(
        GradingScale.school_id == school_id,
        GradingScale.minimum_score <= maximum_score,
        GradingScale.maximum_score >= minimum_score,
    )

    if exclude_id is not None:
        query = query.where(
            GradingScale.id != exclude_id
        )

    return db.scalar(query)


@router.post(
    "",
    response_model=GradingScaleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_grading_scale(
    grading_data: GradingScaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    normalized_grade = grading_data.grade.strip().upper()

    existing_grade = db.scalar(
        select(GradingScale).where(
            GradingScale.school_id == current_user.school_id,
            GradingScale.grade == normalized_grade,
        )
    )

    if existing_grade is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This grade already exists "
                "for this school"
            ),
        )

    overlapping_scale = find_overlapping_scale(
        db=db,
        school_id=current_user.school_id,
        minimum_score=grading_data.minimum_score,
        maximum_score=grading_data.maximum_score,
    )

    if overlapping_scale is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This score range overlaps with "
                f"grade {overlapping_scale.grade}"
            ),
        )

    grading_scale = GradingScale(
        school_id=current_user.school_id,
        grade=normalized_grade,
        minimum_score=grading_data.minimum_score,
        maximum_score=grading_data.maximum_score,
        remark=(
            grading_data.remark.strip()
            if grading_data.remark is not None
            else None
        ),
    )

    db.add(grading_scale)
    db.commit()
    db.refresh(grading_scale)

    return grading_scale


@router.get(
    "",
    response_model=list[GradingScaleResponse],
)
def get_grading_scales(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    grading_scales = db.scalars(
        select(GradingScale)
        .where(
            GradingScale.school_id
            == current_user.school_id
        )
        .order_by(
            GradingScale.minimum_score.desc()
        )
    ).all()

    return grading_scales


@router.get(
    "/{grading_scale_id}",
    response_model=GradingScaleResponse,
)
def get_grading_scale(
    grading_scale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    grading_scale = db.scalar(
        select(GradingScale).where(
            GradingScale.id == grading_scale_id,
            GradingScale.school_id
            == current_user.school_id,
        )
    )

    if grading_scale is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grading scale not found",
        )

    return grading_scale


@router.put(
    "/{grading_scale_id}",
    response_model=GradingScaleResponse,
)
def update_grading_scale(
    grading_scale_id: int,
    grading_data: GradingScaleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    grading_scale = db.scalar(
        select(GradingScale).where(
            GradingScale.id == grading_scale_id,
            GradingScale.school_id
            == current_user.school_id,
        )
    )

    if grading_scale is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grading scale not found",
        )

    new_grade = (
        grading_data.grade.strip().upper()
        if grading_data.grade is not None
        else grading_scale.grade
    )

    new_minimum = (
        grading_data.minimum_score
        if grading_data.minimum_score is not None
        else grading_scale.minimum_score
    )

    new_maximum = (
        grading_data.maximum_score
        if grading_data.maximum_score is not None
        else grading_scale.maximum_score
    )

    if new_minimum > new_maximum:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "minimum_score cannot be greater "
                "than maximum_score"
            ),
        )

    existing_grade = db.scalar(
        select(GradingScale).where(
            GradingScale.school_id
            == current_user.school_id,
            GradingScale.grade == new_grade,
            GradingScale.id != grading_scale_id,
        )
    )

    if existing_grade is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This grade already exists "
                "for this school"
            ),
        )

    overlapping_scale = find_overlapping_scale(
        db=db,
        school_id=current_user.school_id,
        minimum_score=new_minimum,
        maximum_score=new_maximum,
        exclude_id=grading_scale_id,
    )

    if overlapping_scale is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This score range overlaps with "
                f"grade {overlapping_scale.grade}"
            ),
        )

    grading_scale.grade = new_grade
    grading_scale.minimum_score = new_minimum
    grading_scale.maximum_score = new_maximum

    if grading_data.remark is not None:
        grading_scale.remark = grading_data.remark.strip()

    db.commit()
    db.refresh(grading_scale)

    return grading_scale


@router.delete(
    "/{grading_scale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_grading_scale(
    grading_scale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    grading_scale = db.scalar(
        select(GradingScale).where(
            GradingScale.id == grading_scale_id,
            GradingScale.school_id
            == current_user.school_id,
        )
    )

    if grading_scale is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grading scale not found",
        )

    db.delete(grading_scale)
    db.commit()

    return None
