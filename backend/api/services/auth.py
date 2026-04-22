from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import select

from api.config import config
from api.db import get_session
from api.models.annotations import User

security = HTTPBearer()


async def create_jwt_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=config.ACCESS_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user.email,
        "iat": now,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session=Depends(get_session),
) -> User:
    access_token = credentials.credentials

    try:
        payload = jwt.decode(
            access_token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = (
        await session.exec(select(User).where(User.email == payload["sub"]))
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
