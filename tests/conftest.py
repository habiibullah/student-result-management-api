import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

TEST_DATABASE_URL = (
    "postgresql+psycopg://"
    "student_api:student_api_password@"
    "127.0.0.1:5432/student_result_test_db"
)

if "student_result_test_db" not in TEST_DATABASE_URL:
    raise RuntimeError(
        "Tests must only run against student_result_test_db"
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.main import app  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database.connection import SessionLocal  # noqa: E402

from app.models import (  # noqa: E402
    Assessment,
    Class,
    Student,
    Subject,
    Teacher,
)

from app.models.academic_session import AcademicSession  # noqa: E402
from app.models.school import School  # noqa: E402
from app.models.subscription import Subscription  # noqa: E402
from app.models.subscription_plan import SubscriptionPlan  # noqa: E402
from app.models.term import Term  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def clean_test_data():
    yield

    session = SessionLocal()

    try:
        session.execute(
            text(
                """
                TRUNCATE TABLE
                    payment_transactions,
                    published_report_snapshots,
                    result_publications,
                    term_report_comments,
                    student_attendance,
                    student_scores,
                    assessments,
                    teaching_assignments,
                    enrollments,
                    students,
                    teachers,
                    subscriptions,
                    subscription_plans,
                    grading_scales,
                    report_settings,
                    terms,
                    academic_sessions,
                    subjects,
                    classes,
                    users,
                    schools
                RESTART IDENTITY CASCADE
                """
            )
        )

        session.commit()

    finally:
        session.close()


# ============================================================
# USERS AND SCHOOLS
# ============================================================


@pytest.fixture
def platform_admin(db):
    user = User(
        email="platform.admin@example.com",
        password_hash=hash_password(
            "TestPassword123!"
        ),
        role="admin",
        school_id=None,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def inactive_platform_admin(db):
    user = User(
        email="inactive.admin@example.com",
        password_hash=hash_password(
            "TestPassword123!"
        ),
        role="admin",
        school_id=None,
        is_active=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def school_one(db):
    school = School(
        name="Test School One",
        slug="test-school-one",
        email="school.one@example.com",
        is_active=True,
    )

    db.add(school)
    db.commit()
    db.refresh(school)

    return school


@pytest.fixture
def school_two(db):
    school = School(
        name="Test School Two",
        slug="test-school-two",
        email="school.two@example.com",
        is_active=True,
    )

    db.add(school)
    db.commit()
    db.refresh(school)

    return school


@pytest.fixture
def school_admin(
    db,
    school_one,
):
    user = User(
        email="school.admin@example.com",
        password_hash=hash_password(
            "TestPassword123!"
        ),
        role="admin",
        school_id=school_one.id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def second_school_admin(
    db,
    school_one,
):
    user = User(
        email="second.school.admin@example.com",
        password_hash=hash_password(
            "TestPassword123!"
        ),
        role="admin",
        school_id=school_one.id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def other_school_admin(
    db,
    school_two,
):
    user = User(
        email="other.school.admin@example.com",
        password_hash=hash_password(
            "TestPassword123!"
        ),
        role="admin",
        school_id=school_two.id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# CLASSES
# ============================================================


@pytest.fixture
def school_one_class(
    db,
    school_one,
):
    class_ = Class(
        school_id=school_one.id,
        name="Junior Secondary One",
        code="JSS1",
        description="School one test class",
    )

    db.add(class_)
    db.commit()
    db.refresh(class_)

    return class_


@pytest.fixture
def school_two_class(
    db,
    school_two,
):
    class_ = Class(
        school_id=school_two.id,
        name="Junior Secondary One",
        code="JSS1",
        description="School two test class",
    )

    db.add(class_)
    db.commit()
    db.refresh(class_)

    return class_


# ============================================================
# SUBJECTS
# ============================================================


@pytest.fixture
def school_one_subject(
    db,
    school_one,
):
    subject = Subject(
        school_id=school_one.id,
        name="Physics",
        code="PHY",
        description="School one Physics",
    )

    db.add(subject)
    db.commit()
    db.refresh(subject)

    return subject


@pytest.fixture
def school_two_subject(
    db,
    school_two,
):
    subject = Subject(
        school_id=school_two.id,
        name="Physics",
        code="PHY",
        description="School two Physics",
    )

    db.add(subject)
    db.commit()
    db.refresh(subject)

    return subject


# ============================================================
# TEACHERS
# ============================================================


@pytest.fixture
def school_one_teacher(
    db,
    school_one,
):
    user = User(
        email="teacher.one@example.com",
        password_hash=hash_password(
            "TestPassword123!"
        ),
        role="teacher",
        school_id=school_one.id,
        is_active=True,
    )

    db.add(user)
    db.flush()

    teacher = Teacher(
        user_id=user.id,
        school_id=school_one.id,
        employee_number="T001",
        first_name="Teacher",
        last_name="One",
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher


@pytest.fixture
def school_two_teacher(
    db,
    school_two,
):
    user = User(
        email="teacher.two@example.com",
        password_hash=hash_password(
            "TestPassword123!"
        ),
        role="teacher",
        school_id=school_two.id,
        is_active=True,
    )

    db.add(user)
    db.flush()

    teacher = Teacher(
        user_id=user.id,
        school_id=school_two.id,
        employee_number="T001",
        first_name="Teacher",
        last_name="Two",
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher


# ============================================================
# STUDENTS
# ============================================================


@pytest.fixture
def school_one_student(
    db,
    school_one,
):
    student = Student(
        user_id=None,
        school_id=school_one.id,
        admission_number="SCH1/001",
        first_name="Aisha",
        last_name="Yusuf",
        date_of_birth=None,
        gender=None,
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return student


@pytest.fixture
def school_two_student(
    db,
    school_two,
):
    student = Student(
        user_id=None,
        school_id=school_two.id,
        admission_number="SCH2/001",
        first_name="Fatimah",
        last_name="Ibrahim",
        date_of_birth=None,
        gender=None,
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return student


# ============================================================
# ACADEMIC SESSIONS
# ============================================================


@pytest.fixture
def academic_session_one(
    db,
    school_one,
):
    session = AcademicSession(
        school_id=school_one.id,
        name="2026/2027",
        is_current=False,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@pytest.fixture
def academic_session_two(
    db,
    school_two,
):
    session = AcademicSession(
        school_id=school_two.id,
        name="2026/2027",
        is_current=False,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


# ============================================================
# TERMS
# ============================================================


@pytest.fixture
def first_term(
    db,
    academic_session_one,
):
    term = Term(
        academic_session_id=academic_session_one.id,
        name="First Term",
    )

    db.add(term)
    db.commit()
    db.refresh(term)

    return term


@pytest.fixture
def second_term(
    db,
    academic_session_one,
):
    term = Term(
        academic_session_id=academic_session_one.id,
        name="Second Term",
    )

    db.add(term)
    db.commit()
    db.refresh(term)

    return term


@pytest.fixture
def third_term(
    db,
    academic_session_one,
):
    term = Term(
        academic_session_id=academic_session_one.id,
        name="Third Term",
    )

    db.add(term)
    db.commit()
    db.refresh(term)

    return term


@pytest.fixture
def test_extra_term(
    db,
    academic_session_one,
):
    term = Term(
        academic_session_id=academic_session_one.id,
        name="Test Extra Term",
    )

    db.add(term)
    db.commit()
    db.refresh(term)

    return term


@pytest.fixture
def unsubscribed_term(
    db,
    academic_session_one,
):
    term = Term(
        academic_session_id=academic_session_one.id,
        name="Unsubscribed Term",
    )

    db.add(term)
    db.commit()
    db.refresh(term)

    return term


@pytest.fixture
def school_two_term(
    db,
    academic_session_two,
):
    term = Term(
        academic_session_id=academic_session_two.id,
        name="First Term",
    )

    db.add(term)
    db.commit()
    db.refresh(term)

    return term


# ============================================================
# SUBSCRIPTION PLAN
# ============================================================


@pytest.fixture
def basic_subscription_plan(db):
    plan = SubscriptionPlan(
        name="Basic Test Plan",
        description="Automated test subscription plan",
        price_per_term=Decimal("20000.00"),
        max_students=200,
        is_active=True,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


# ============================================================
# SUBSCRIPTIONS
# ============================================================


@pytest.fixture
def active_subscription(
    db,
    school_one,
    academic_session_one,
    first_term,
    basic_subscription_plan,
):
    subscription = Subscription(
        school_id=school_one.id,
        subscription_plan_id=basic_subscription_plan.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        status="active",
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


@pytest.fixture
def pending_subscription(
    db,
    school_one,
    academic_session_one,
    second_term,
    basic_subscription_plan,
):
    subscription = Subscription(
        school_id=school_one.id,
        subscription_plan_id=basic_subscription_plan.id,
        academic_session_id=academic_session_one.id,
        term_id=second_term.id,
        status="pending",
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


@pytest.fixture
def cancelled_subscription(
    db,
    school_one,
    academic_session_one,
    third_term,
    basic_subscription_plan,
):
    subscription = Subscription(
        school_id=school_one.id,
        subscription_plan_id=basic_subscription_plan.id,
        academic_session_id=academic_session_one.id,
        term_id=third_term.id,
        status="cancelled",
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


@pytest.fixture
def expired_subscription(
    db,
    school_one,
    academic_session_one,
    test_extra_term,
    basic_subscription_plan,
):
    subscription = Subscription(
        school_id=school_one.id,
        subscription_plan_id=basic_subscription_plan.id,
        academic_session_id=academic_session_one.id,
        term_id=test_extra_term.id,
        status="expired",
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


@pytest.fixture
def school_two_subscription(
    db,
    school_two,
    academic_session_two,
    school_two_term,
    basic_subscription_plan,
):
    subscription = Subscription(
        school_id=school_two.id,
        subscription_plan_id=basic_subscription_plan.id,
        academic_session_id=academic_session_two.id,
        term_id=school_two_term.id,
        status="active",
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


# ============================================================
# ASSESSMENTS
# ============================================================


@pytest.fixture
def active_term_assessment(
    db,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
    active_subscription,
):
    assessment = Assessment(
        class_id=school_one_class.id,
        subject_id=school_one_subject.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        assessment_type="CA",
        sequence=1,
        name="First CA",
        max_score=10,
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment


@pytest.fixture
def pending_term_assessment(
    db,
    school_one_class,
    school_one_subject,
    academic_session_one,
    second_term,
    pending_subscription,
):
    assessment = Assessment(
        class_id=school_one_class.id,
        subject_id=school_one_subject.id,
        academic_session_id=academic_session_one.id,
        term_id=second_term.id,
        assessment_type="CA",
        sequence=1,
        name="Pending Term CA",
        max_score=10,
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment


@pytest.fixture
def school_two_assessment(
    db,
    school_two_class,
    school_two_subject,
    academic_session_two,
    school_two_term,
    school_two_subscription,
):
    assessment = Assessment(
        class_id=school_two_class.id,
        subject_id=school_two_subject.id,
        academic_session_id=academic_session_two.id,
        term_id=school_two_term.id,
        assessment_type="CA",
        sequence=1,
        name="School Two CA",
        max_score=10,
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment
