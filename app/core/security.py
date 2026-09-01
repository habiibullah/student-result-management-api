from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(
    subject: str,
    role: str,
    secret_key: str,
    expires_minutes: int,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes
    )

    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm="HS256",
    )
