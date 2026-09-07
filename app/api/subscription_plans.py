from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_platform_admin,
)
from app.database.connection import get_db
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.schemas.subscription_plan import (
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdate,
)


router = APIRouter(
    prefix="/api/subscription-plans",
    tags=["Subscription Plans"],
)


@router.post(
    "",
    response_model=SubscriptionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subscription_plan(
    payload: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_platform_admin
    ),
):
    normalized_name = payload.name.strip()

    existing_plan = db.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.name == normalized_name
        )
    )

    if existing_plan is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A subscription plan with this name already exists",
        )

    plan = SubscriptionPlan(
        name=normalized_name,
        description=(
            payload.description.strip()
            if payload.description is not None
            else None
        ),
        price_per_term=payload.price_per_term,
        max_students=payload.max_students,
        is_active=payload.is_active,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


@router.get(
    "",
    response_model=list[SubscriptionPlanResponse],
)
def list_subscription_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    statement = select(
        SubscriptionPlan
    ).order_by(
        SubscriptionPlan.price_per_term.asc()
    )

    if not (
        current_user.role == "admin"
        and current_user.school_id is None
    ):
        statement = statement.where(
            SubscriptionPlan.is_active.is_(True)
        )

    return list(
        db.scalars(statement).all()
    )


@router.get(
    "/{plan_id}",
    response_model=SubscriptionPlanResponse,
)
def get_subscription_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    plan = db.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id == plan_id
        )
    )

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found",
        )

    is_platform_admin = (
        current_user.role == "admin"
        and current_user.school_id is None
    )

    if not plan.is_active and not is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found",
        )

    return plan


@router.patch(
    "/{plan_id}",
    response_model=SubscriptionPlanResponse,
)
def update_subscription_plan(
    plan_id: int,
    payload: SubscriptionPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_platform_admin
    ),
):
    plan = db.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id == plan_id
        )
    )

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found",
        )

    updates = payload.model_dump(
        exclude_unset=True
    )

    if "name" in updates:
        normalized_name = updates["name"].strip()

        duplicate = db.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.name
                == normalized_name,
                SubscriptionPlan.id != plan_id,
            )
        )

        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A subscription plan "
                    "with this name already exists"
                ),
            )

        plan.name = normalized_name

    if "description" in updates:
        plan.description = (
            updates["description"].strip()
            if updates["description"]
            is not None
            else None
        )

    if "price_per_term" in updates:
        plan.price_per_term = (
            updates["price_per_term"]
        )

    if "max_students" in updates:
        plan.max_students = updates[
            "max_students"
        ]

    if "is_active" in updates:
        plan.is_active = updates[
            "is_active"
        ]

    db.commit()
    db.refresh(plan)

    return plan
