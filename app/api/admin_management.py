from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import (
    require_admin,
    require_platform_admin,
)
from app.core.security import hash_password
from app.database.connection import get_db
from app.models.school import School
from app.models.user import User
from app.schemas.admin_management import (
    AdminStatusUpdate,
    AdminUserResponse,
    PlatformAdminCreate,
    SchoolAdminCreate,
)


router = APIRouter(
    prefix="/api/admin-management",
    tags=["Admin Management"],
)


def build_admin_response(
    user: User,
) -> AdminUserResponse:
    account_type = (
        "platform_admin"
        if user.school_id is None
        else "school_admin"
    )

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        account_type=account_type,
        school_id=user.school_id,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post(
    "/platform-admins",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_platform_admin(
    payload: PlatformAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    normalized_email = payload.email.strip().lower()

    existing_user = db.scalar(
        select(User).where(
            User.email == normalized_email
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    admin = User(
        email=normalized_email,
        password_hash=hash_password(
            payload.password
        ),
        role="admin",
        school_id=None,
        is_active=True,
    )

    try:
        db.add(admin)
        db.commit()
        db.refresh(admin)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    except Exception:
        db.rollback()
        raise

    return build_admin_response(admin)


@router.get(
    "/platform-admins",
    response_model=list[AdminUserResponse],
)
def list_platform_admins(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    admins = db.scalars(
        select(User)
        .where(
            User.role == "admin",
            User.school_id.is_(None),
        )
        .order_by(User.created_at.asc())
    ).all()

    return [
        build_admin_response(admin)
        for admin in admins
    ]


@router.post(
    "/school-admins",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_school_admin(
    payload: SchoolAdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    normalized_email = payload.email.strip().lower()

    existing_user = db.scalar(
        select(User).where(
            User.email == normalized_email
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Platform admin must explicitly specify the school.
    if current_user.school_id is None:
        if payload.school_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "school_id is required when a platform "
                    "admin creates a school admin"
                ),
            )

        target_school_id = payload.school_id

    else:
        # A school admin can create admins only for their
        # own school.
        if (
            payload.school_id is not None
            and payload.school_id
            != current_user.school_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You cannot create an administrator "
                    "for another school"
                ),
            )

        target_school_id = current_user.school_id

    school = db.scalar(
        select(School).where(
            School.id == target_school_id
        )
    )

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    if not school.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot create an admin for an inactive school",
        )

    admin = User(
        email=normalized_email,
        password_hash=hash_password(
            payload.password
        ),
        role="admin",
        school_id=target_school_id,
        is_active=True,
    )

    try:
        db.add(admin)
        db.commit()
        db.refresh(admin)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    except Exception:
        db.rollback()
        raise

    return build_admin_response(admin)


@router.get(
    "/school-admins",
    response_model=list[AdminUserResponse],
)
def list_school_admins(
    school_id: int | None = Query(
        default=None,
        ge=1,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Platform administrators may view all schools or
    # filter by a particular school.
    if current_user.school_id is None:
        statement = select(User).where(
            User.role == "admin",
            User.school_id.is_not(None),
        )

        if school_id is not None:
            statement = statement.where(
                User.school_id == school_id
            )

    else:
        # School administrators can view only their
        # own school's administrators.
        if (
            school_id is not None
            and school_id != current_user.school_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You cannot view administrators "
                    "from another school"
                ),
            )

        statement = select(User).where(
            User.role == "admin",
            User.school_id
            == current_user.school_id,
        )

    admins = db.scalars(
        statement.order_by(
            User.created_at.asc()
        )
    ).all()

    return [
        build_admin_response(admin)
        for admin in admins
    ]


@router.patch(
    "/platform-admins/{admin_id}/status",
    response_model=AdminUserResponse,
)
def update_platform_admin_status(
    admin_id: int,
    payload: AdminStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    admin = db.scalar(
        select(User).where(
            User.id == admin_id,
            User.role == "admin",
            User.school_id.is_(None),
        )
    )

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform administrator not found",
        )

    # Prevent a platform admin from disabling
    # their own currently authenticated account.
    if (
        admin.id == current_user.id
        and payload.is_active is False
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "You cannot deactivate your own "
                "platform administrator account"
            ),
        )

    if (
        admin.is_active
        and payload.is_active is False
    ):
        active_admin_count = db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.role == "admin",
                User.school_id.is_(None),
                User.is_active.is_(True),
            )
        )

        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "The last active platform administrator "
                    "cannot be deactivated"
                ),
            )

    admin.is_active = payload.is_active

    db.commit()
    db.refresh(admin)

    return build_admin_response(admin)



@router.patch(
    "/school-admins/{admin_id}/status",
    response_model=AdminUserResponse,
)
def update_school_admin_status(
    admin_id: int,
    payload: AdminStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    admin = db.scalar(
        select(User).where(
            User.id == admin_id,
            User.role == "admin",
            User.school_id.is_not(None),
        )
    )

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School administrator not found",
        )

    # School administrators can manage only
    # administrators belonging to their own school.
    if current_user.school_id is not None:
        if admin.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You cannot manage an administrator "
                    "from another school"
                ),
            )

        # Prevent school admins from disabling
        # their own currently authenticated account.
        if (
            admin.id == current_user.id
            and payload.is_active is False
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "You cannot deactivate your own "
                    "school administrator account"
                ),
            )

    if (
        admin.is_active
        and payload.is_active is False
    ):
        active_admin_count = db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.role == "admin",
                User.school_id == admin.school_id,
                User.is_active.is_(True),
            )
        )

        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "The last active administrator "
                    "for this school cannot be deactivated"
                ),
            )

    admin.is_active = payload.is_active

    db.commit()
    db.refresh(admin)

    return build_admin_response(admin)
