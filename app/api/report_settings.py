from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models.report_settings import ReportSettings
from app.models.user import User
from app.schemas.report_settings import (
    ReportSettingsCreate,
    ReportSettingsResponse,
    ReportSettingsUpdate,
)


router = APIRouter(
    prefix="/api/report-settings",
    tags=["Report Settings"],
)


@router.get(
    "",
    response_model=ReportSettingsResponse,
)
def get_report_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    settings = db.scalar(
        select(ReportSettings).where(
            ReportSettings.school_id
            == current_user.school_id
        )
    )

    if settings is None:
        settings = ReportSettings(
            school_id=current_user.school_id,
        )

        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


@router.post(
    "",
    response_model=ReportSettingsResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_report_settings(
    settings_data: ReportSettingsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    existing = db.scalar(
        select(ReportSettings).where(
            ReportSettings.school_id
            == current_user.school_id
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Report settings already exist "
                "for this school"
            ),
        )

    settings = ReportSettings(
        school_id=current_user.school_id,
        **settings_data.model_dump(),
    )

    db.add(settings)
    db.commit()
    db.refresh(settings)

    return settings


@router.patch(
    "",
    response_model=ReportSettingsResponse,
)
def update_report_settings(
    settings_data: ReportSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    settings = db.scalar(
        select(ReportSettings).where(
            ReportSettings.school_id
            == current_user.school_id
        )
    )

    if settings is None:
        settings = ReportSettings(
            school_id=current_user.school_id,
        )

        db.add(settings)
        db.flush()

    update_data = settings_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            settings,
            field,
            value,
        )

    db.commit()
    db.refresh(settings)

    return settings
