from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import (
    require_platform_admin,
    require_school_admin,
)
from app.core.security import hash_password
from app.core.school_logo_storage import (
    MAX_LOGO_BYTES,
    school_logo_directory,
    validate_school_logo,
)
from app.database.connection import get_db
from app.models.school import School
from app.models.user import User
from app.schemas.school import (
    SchoolRegistrationRequest,
    SchoolRegistrationResponse,
    SchoolResponse,
    SchoolStatusUpdate,
    SchoolUpdate,
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
    current_user: User = Depends(require_platform_admin),
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



@router.get(
    "",
    response_model=list[SchoolResponse],
)
def list_schools(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    statement = select(School).order_by(
        School.name.asc(),
        School.id.asc(),
    )

    schools = db.scalars(statement).all()

    return list(schools)


@router.get(
    "/me",
    response_model=SchoolResponse,
)
def get_my_school(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    school = db.scalar(
        select(School).where(
            School.id == current_user.school_id
        )
    )

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    return school


@router.patch(
    "/me",
    response_model=SchoolResponse,
)
def update_my_school(
    payload: SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    school = db.scalar(
        select(School).where(
            School.id == current_user.school_id
        )
    )

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    update_data = payload.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()

        setattr(
            school,
            field,
            value,
        )

    db.commit()
    db.refresh(school)

    return school


@router.post(
    "/me/logo",
    response_model=SchoolResponse,
)
def upload_my_school_logo(
    logo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    school = db.scalar(
        select(School).where(
            School.id == current_user.school_id
        )
    )

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    try:
        content = logo.file.read(MAX_LOGO_BYTES + 1)
        normalized_logo = validate_school_logo(content)
    finally:
        logo.file.close()

    logo_directory = school_logo_directory()
    logo_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = f"school_{school.id}_{uuid4().hex}.jpg"
    new_logo_path = logo_directory / filename

    try:
        new_logo_path.write_bytes(normalized_logo)
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save school logo",
        )

    school.logo_url = "/api/schools/me/logo"

    try:
        db.commit()
        db.refresh(school)
    except Exception:
        db.rollback()
        new_logo_path.unlink(missing_ok=True)
        raise

    for old_path in logo_directory.glob(
        f"school_{school.id}_*.jpg"
    ):
        if old_path != new_logo_path:
            old_path.unlink(missing_ok=True)

    return school

@router.get(
    "/me/logo",
)
def get_my_school_logo(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    school = db.scalar(
        select(School).where(
            School.id == current_user.school_id
        )
    )

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    logo_directory = school_logo_directory()

    logo_files = sorted(
        logo_directory.glob(
            f"school_{school.id}_*.jpg"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not school.logo_url or not logo_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School logo not found",
        )

    return FileResponse(
        path=logo_files[0],
        media_type="image/jpeg",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete(
    "/me/logo",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_my_school_logo(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    school = db.scalar(
        select(School).where(
            School.id == current_user.school_id
        )
    )

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    logo_directory = school_logo_directory()

    logo_files = list(
        logo_directory.glob(
            f"school_{school.id}_*.jpg"
        )
    )

    school.logo_url = None

    try:
        db.commit()
        db.refresh(school)
    except Exception:
        db.rollback()
        raise

    for logo_path in logo_files:
        logo_path.unlink(missing_ok=True)


@router.get(
    "/{school_id}",
    response_model=SchoolResponse,
)
def get_school_by_id(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    school = db.scalar(
        select(School).where(
            School.id == school_id
        )
    )

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    return school


@router.patch(
    "/{school_id}",
    response_model=SchoolResponse,
)
def update_school_by_id(
    school_id: int,
    payload: SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    school = db.scalar(
        select(School).where(
            School.id == school_id
        )
    )

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    update_data = payload.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()

        setattr(
            school,
            field,
            value,
        )

    db.commit()
    db.refresh(school)

    return school


@router.patch(
    "/{school_id}/status",
    response_model=SchoolResponse,
)
def update_school_status(
    school_id: int,
    payload: SchoolStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    school = db.scalar(
        select(School).where(
            School.id == school_id
        )
    )

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    school.is_active = payload.is_active

    db.commit()
    db.refresh(school)

    return school
