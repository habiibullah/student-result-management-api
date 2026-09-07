from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_school_admin,
)
from app.core.security import hash_password
from app.database.connection import get_db
from app.models import TeachingAssignment, Teacher, User
from app.schemas.teacher import (
    TeacherCreate,
    TeacherResponse,
    TeacherUpdate,
)


router = APIRouter(
    prefix="/api/teachers",
    tags=["Teachers"],
)


@router.post(
    "",
    response_model=TeacherResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_teacher(
    teacher_data: TeacherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. CHECK EMAIL UNIQUENESS
    # ---------------------------------------------------------

    existing_user = db.scalar(
        select(User).where(
            User.email == teacher_data.email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    # ---------------------------------------------------------
    # 2. CHECK EMPLOYEE NUMBER WITHIN CURRENT SCHOOL
    # ---------------------------------------------------------

    existing_teacher = db.scalar(
        select(Teacher).where(
            Teacher.employee_number
            == teacher_data.employee_number,
            Teacher.school_id
            == current_user.school_id,
        )
    )

    if existing_teacher:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Teacher with this employee number "
                "already exists in this school"
            ),
        )

    # ---------------------------------------------------------
    # 3. CREATE TEACHER USER ACCOUNT
    # ---------------------------------------------------------

    user = User(
        email=teacher_data.email,
        password_hash=hash_password(
            teacher_data.password
        ),
        role="teacher",
        is_active=True,
        school_id=current_user.school_id,
    )

    db.add(user)
    db.flush()

    # ---------------------------------------------------------
    # 4. CREATE TEACHER PROFILE
    # ---------------------------------------------------------

    teacher = Teacher(
        user_id=user.id,
        school_id=current_user.school_id,
        employee_number=teacher_data.employee_number,
        first_name=teacher_data.first_name,
        last_name=teacher_data.last_name,
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher


@router.get(
    "",
    response_model=list[TeacherResponse],
)
def get_teachers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    teachers = db.scalars(
        select(Teacher)
        .where(
            Teacher.school_id
            == current_user.school_id
        )
        .order_by(
            Teacher.last_name,
            Teacher.first_name,
        )
    ).all()

    return teachers


@router.get(
    "/{teacher_id}",
    response_model=TeacherResponse,
)
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    teacher = db.scalar(
        select(Teacher).where(
            Teacher.id == teacher_id,
            Teacher.school_id
            == current_user.school_id,
        )
    )

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    return teacher


@router.put(
    "/{teacher_id}",
    response_model=TeacherResponse,
)
def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. GET TEACHER FROM CURRENT SCHOOL
    # ---------------------------------------------------------

    teacher = db.scalar(
        select(Teacher).where(
            Teacher.id == teacher_id,
            Teacher.school_id
            == current_user.school_id,
        )
    )

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    # ---------------------------------------------------------
    # 2. GET ASSOCIATED USER FROM CURRENT SCHOOL
    # ---------------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.id == teacher.user_id,
            User.school_id
            == current_user.school_id,
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher user account not found",
        )

    # ---------------------------------------------------------
    # 3. UPDATE EMAIL
    # ---------------------------------------------------------

    if teacher_data.email is not None:
        existing_user = db.scalar(
            select(User).where(
                User.email == teacher_data.email,
                User.id != teacher.user_id,
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        user.email = teacher_data.email

    # ---------------------------------------------------------
    # 4. UPDATE EMPLOYEE NUMBER
    # ---------------------------------------------------------

    if teacher_data.employee_number is not None:
        existing_teacher = db.scalar(
            select(Teacher).where(
                Teacher.employee_number
                == teacher_data.employee_number,
                Teacher.school_id
                == current_user.school_id,
                Teacher.id != teacher_id,
            )
        )

        if existing_teacher:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Teacher with this employee number "
                    "already exists in this school"
                ),
            )

        teacher.employee_number = (
            teacher_data.employee_number
        )

    # ---------------------------------------------------------
    # 5. UPDATE PROFILE
    # ---------------------------------------------------------

    if teacher_data.first_name is not None:
        teacher.first_name = teacher_data.first_name

    if teacher_data.last_name is not None:
        teacher.last_name = teacher_data.last_name

    if teacher_data.is_active is not None:
        user.is_active = teacher_data.is_active

    db.commit()
    db.refresh(teacher)

    return teacher


@router.delete(
    "/{teacher_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    # ---------------------------------------------------------
    # 1. GET TEACHER FROM CURRENT SCHOOL
    # ---------------------------------------------------------

    teacher = db.scalar(
        select(Teacher).where(
            Teacher.id == teacher_id,
            Teacher.school_id
            == current_user.school_id,
        )
    )

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    # ---------------------------------------------------------
    # 2. CHECK TEACHING ASSIGNMENTS
    # ---------------------------------------------------------

    assignment_count = db.scalar(
        select(
            func.count(TeachingAssignment.id)
        ).where(
            TeachingAssignment.teacher_id
            == teacher.id
        )
    )

    if assignment_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Teacher cannot be deleted because they have "
                "teaching assignments. Deactivate the teacher instead."
            ),
        )

    # ---------------------------------------------------------
    # 3. GET ASSOCIATED USER FROM CURRENT SCHOOL
    # ---------------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.id == teacher.user_id,
            User.school_id
            == current_user.school_id,
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher user account not found",
        )

    # ---------------------------------------------------------
    # 4. DELETE TEACHER AND USER
    # ---------------------------------------------------------

    # Delete Teacher first because teacher.user_id
    # is non-nullable.
    db.delete(teacher)
    db.flush()

    # Then delete associated User.
    db.delete(user)

    db.commit()

    return None
