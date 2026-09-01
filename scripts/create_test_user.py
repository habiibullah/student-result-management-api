from sqlalchemy import select

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models import User


def main():
    db = SessionLocal()

    try:
        email = "admin@example.com"

        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            print("Test admin user already exists.")
            return

        user = User(
            email=email,
            password_hash=hash_password("AdminPassword123"),
            role="admin",
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"Test admin user created successfully. ID: {user.id}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
