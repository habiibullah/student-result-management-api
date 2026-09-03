from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.database.connection import get_db
from app.models import Class, TeachingAssignment, User
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
    current_user: User = Depends(require_admin),
):
    existing_class = db.scalar(
        select(Class).where(Class.code == class_data.code)
    )

    if existing_class:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class with this code already exists",
        )

    class_ = Class(
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
    classes = db.scalars(
        select(Class).order_by(Class.name)
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
    class_ = db.scalar(
        select(Class).where(Class.id == class_id)
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
    current_user: User = Depends(require_admin),
):
    class_ = db.scalar(
        select(Class).where(Class.id == class_id)
    )

    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    if class_data.code is not None:
        existing_class = db.scalar(
            select(Class).where(
                (Class.code == class_data.code)
                & (Class.id != class_id)
            )
        )

        if existing_class:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Class with this code already exists",
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
    current_user: User = Depends(require_admin),
):
    class_ = db.scalar(
        select(Class).where(Class.id == class_id)
    )

    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    assignment_count = db.scalar(
        select(func.count(TeachingAssignment.id)).where(
            TeachingAssignment.class_id == class_id
        )
    )

    if assignment_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Class cannot be deleted because it has "
                "teaching assignments. Delete the assignments first."
            ),
        )

    db.delete(class_)
    db.commit()

    return None
