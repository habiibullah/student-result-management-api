from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_school_admin,
)
from app.database.connection import get_db
from app.models.performance_comment_band import PerformanceCommentBand
from app.models.user import User
from app.schemas.performance_comment_band import (
    PerformanceCommentBandCreate,
    PerformanceCommentBandResponse,
    PerformanceCommentBandUpdate,
)


router = APIRouter(
    prefix="/api/performance-comment-bands",
    tags=["Performance Comment Bands"],
)


def find_overlapping_band(
    db: Session,
    school_id: int,
    minimum_average: float,
    maximum_average: float,
    exclude_id: int | None = None,
):
    query = select(PerformanceCommentBand).where(
        PerformanceCommentBand.school_id == school_id,
        PerformanceCommentBand.minimum_average <= maximum_average,
        PerformanceCommentBand.maximum_average >= minimum_average,
    )

    if exclude_id is not None:
        query = query.where(
            PerformanceCommentBand.id != exclude_id
        )

    return db.scalar(query)


@router.post(
    "",
    response_model=PerformanceCommentBandResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_performance_comment_band(
    band_data: PerformanceCommentBandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    overlapping_band = find_overlapping_band(
        db=db,
        school_id=current_user.school_id,
        minimum_average=band_data.minimum_average,
        maximum_average=band_data.maximum_average,
    )

    if overlapping_band is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This average range overlaps with "
                "an existing performance comment band"
            ),
        )

    band = PerformanceCommentBand(
        school_id=current_user.school_id,
        minimum_average=band_data.minimum_average,
        maximum_average=band_data.maximum_average,
        teacher_comment=band_data.teacher_comment.strip(),
        principal_comment=band_data.principal_comment.strip(),
    )

    db.add(band)
    db.commit()
    db.refresh(band)

    return band


@router.get(
    "",
    response_model=list[PerformanceCommentBandResponse],
)
def get_performance_comment_bands(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    return db.scalars(
        select(PerformanceCommentBand)
        .where(
            PerformanceCommentBand.school_id
            == current_user.school_id
        )
        .order_by(
            PerformanceCommentBand.minimum_average.desc()
        )
    ).all()


@router.get(
    "/{band_id}",
    response_model=PerformanceCommentBandResponse,
)
def get_performance_comment_band(
    band_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    band = db.scalar(
        select(PerformanceCommentBand).where(
            PerformanceCommentBand.id == band_id,
            PerformanceCommentBand.school_id
            == current_user.school_id,
        )
    )

    if band is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance comment band not found",
        )

    return band


@router.put(
    "/{band_id}",
    response_model=PerformanceCommentBandResponse,
)
def update_performance_comment_band(
    band_id: int,
    band_data: PerformanceCommentBandUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    band = db.scalar(
        select(PerformanceCommentBand).where(
            PerformanceCommentBand.id == band_id,
            PerformanceCommentBand.school_id
            == current_user.school_id,
        )
    )

    if band is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance comment band not found",
        )

    new_minimum = (
        band_data.minimum_average
        if band_data.minimum_average is not None
        else band.minimum_average
    )

    new_maximum = (
        band_data.maximum_average
        if band_data.maximum_average is not None
        else band.maximum_average
    )

    if new_minimum > new_maximum:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "minimum_average cannot be greater "
                "than maximum_average"
            ),
        )

    overlapping_band = find_overlapping_band(
        db=db,
        school_id=current_user.school_id,
        minimum_average=new_minimum,
        maximum_average=new_maximum,
        exclude_id=band_id,
    )

    if overlapping_band is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This average range overlaps with "
                "an existing performance comment band"
            ),
        )

    band.minimum_average = new_minimum
    band.maximum_average = new_maximum

    if band_data.teacher_comment is not None:
        band.teacher_comment = band_data.teacher_comment.strip()

    if band_data.principal_comment is not None:
        band.principal_comment = band_data.principal_comment.strip()

    db.commit()
    db.refresh(band)

    return band


@router.delete(
    "/{band_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_performance_comment_band(
    band_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    band = db.scalar(
        select(PerformanceCommentBand).where(
            PerformanceCommentBand.id == band_id,
            PerformanceCommentBand.school_id
            == current_user.school_id,
        )
    )

    if band is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performance comment band not found",
        )

    db.delete(band)
    db.commit()

    return None
