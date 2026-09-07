from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.connection import get_db
from app.models.school import School
from app.models.user import User
from app.schemas.school import (
    SchoolRegistrationRequest,
    SchoolRegistrationResponse,
)


router = APIRouter(
    prefix="/api/schools",
    tags=["Schools"],
)


@router.post(
    "/register",
    response_model=SchoolRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_school(
    payload: SchoolRegistrationRequest,
    db: Session = Depends(get_db),
):
    normalized_slug = payload.school_slug.strip().lower()
    normalized_admin_email = str(
        payload.admin_email
    ).strip().lower()

    normalized_school_email = (
        str(payload.school_email).strip().lower()
        if payload.school_email is not None
        else None
    )

    existing_school = db.scalar(
        select(School).where(
            School.slug == normalized_slug
        )
    )

    if existing_school is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A school with this slug already exists",
        )

    existing_user = db.scalar(
        select(User).where(
            User.email == normalized_admin_email
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    school = School(
        name=payload.school_name.strip(),
        slug=normalized_slug,
        email=normalized_school_email,
        phone=(
            payload.phone.strip()
            if payload.phone is not None
            else None
        ),
        address=(
            payload.address.strip()
            if payload.address is not None
            else None
        ),
        motto=(
            payload.motto.strip()
            if payload.motto is not None
            else None
        ),
        is_active=True,
    )

    try:
        db.add(school)

        # Flush creates the school ID without committing yet.
        db.flush()

        school_admin = User(
            email=normalized_admin_email,
            password_hash=hash_password(
                payload.admin_password
            ),
            role="admin",
            is_active=True,
            school_id=school.id,
        )

        db.add(school_admin)

        # Flush again so admin ID is available.
        db.flush()

        school_id = school.id
        admin_user_id = school_admin.id

        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "School registration could not be completed "
                "because some registration information already exists"
            ),
        )

    except Exception:
        db.rollback()
        raise

    return SchoolRegistrationResponse(
        school_id=school_id,
        school_name=school.name,
        school_slug=school.slug,
        school_email=school.email,
        admin_user_id=admin_user_id,
        admin_email=school_admin.email,
        role=school_admin.role,
        message="School registered successfully",
    )
