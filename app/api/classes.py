from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_school_admin,
)
from app.database.connection import get_db
from app.models import (
    Assessment,
    Class,
    Enrollment,
    ResultPublication,
    TeachingAssignment,
    User,
)
from app.schemas.class_model import (
    ClassCreate,
    ClassResponse,
    ClassUpdate,
)

router = APIRouter(
    prefix="/api/classes",
    tags=["Classes"],
)


@router.post(
    "",
    response_model=ClassResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class(
    class_data: ClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    existing_class = db.scalar(
        select(Class).where(
            Class.code == class_data.code,
            Class.school_id == current_user.school_id,
        )
    )

    if existing_class:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class with this code already exists in this school",
        )

    class_ = Class(
        school_id=current_user.school_id,
        name=class_data.name,
        code=class_data.code,
        description=class_data.description,
    )

    db.add(class_)
    db.commit()
    db.refresh(class_)

    return class_


@router.get(
    "",
    response_model=list[ClassResponse],
)
def get_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    classes = db.scalars(
        select(Class)
        .where(
            Class.school_id == current_user.school_id
        )
        .order_by(Class.name)
    ).all()

    return classes


@router.get(
    "/{class_id}",
    response_model=ClassResponse,
)
def get_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    class_ = db.scalar(
        select(Class).where(
            Class.id == class_id,
            Class.school_id == current_user.school_id,
        )
    )

    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    return class_


@router.put(
    "/{class_id}",
    response_model=ClassResponse,
)
def update_class(
    class_id: int,
    class_data: ClassUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    class_ = db.scalar(
        select(Class).where(
            Class.id == class_id,
            Class.school_id == current_user.school_id,
        )
    )

    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    if class_data.code is not None:
        existing_class = db.scalar(
            select(Class).where(
                Class.code == class_data.code,
                Class.school_id == current_user.school_id,
                Class.id != class_id,
            )
        )

        if existing_class:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Class with this code already exists in this school",
            )

        class_.code = class_data.code

    if class_data.name is not None:
        class_.name = class_data.name

    if class_data.description is not None:
        class_.description = class_data.description

    db.commit()
    db.refresh(class_)

    return class_


@router.delete(
    "/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    class_ = db.scalar(
        select(Class).where(
            Class.id == class_id,
            Class.school_id == current_user.school_id,
        )
    )

    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    assignment_count = db.scalar(
        select(func.count(TeachingAssignment.id)).where(
            TeachingAssignment.class_id == class_.id
        )
    )

    enrollment_count = db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.class_id == class_.id
        )
    )

    assessment_count = db.scalar(
        select(func.count(Assessment.id)).where(
            Assessment.class_id == class_.id
        )
    )

    publication_count = db.scalar(
        select(func.count(ResultPublication.id)).where(
            ResultPublication.class_id == class_.id
        )
    )

    if (
       assignment_count > 0
       or enrollment_count > 0
       or assessment_count > 0
       or publication_count > 0
    ):
       raise HTTPException(
           status_code=status.HTTP_409_CONFLICT,
           detail=(
               "Class cannot be deleted because it already has "
               "academic records or related assignments."
           ),
       )

    db.delete(class_)
    db.commit()

    return None
