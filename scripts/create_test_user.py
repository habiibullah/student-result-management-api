from sqlalchemy import select

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models import User


TEST_USERS = [
    {
        "email": "teacher@example.com",
        "password": "TeacherPassword123",
        "role": "teacher",
    },
    {
        "email": "student@example.com",
        "password": "StudentPassword123",
        "role": "student",
    },
]


def main():
    db = SessionLocal()

    try:
        for user_data in TEST_USERS:
            existing_user = db.scalar(
                select(User).where(
                    User.email == user_data["email"]
                )
            )

            if existing_user:
                print(
                    f"User already exists: {user_data['email']}"
                )
                continue

            user = User(
                email=user_data["email"],
                password_hash=hash_password(
                    user_data["password"]
                ),
                role=user_data["role"],
                is_active=True,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            print(
                f"Created {user.role} user: "
                f"{user.email} (ID: {user.id})"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()
