"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import select

from api.config import config
from api.db import get_session
from api.models.annotations import User
from api.models.auth import LoginRequest, LoginResponse

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session=Depends(get_session),
) -> User:
    provided_code = credentials.credentials

    is_reviewer = provided_code in config.CODES_REVIEWERS
    is_annotator = provided_code in config.CODES_ANNOTATORS

    if not is_reviewer and not is_annotator:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication code",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = (await session.exec(select(User))).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, session=Depends(get_session)) -> LoginResponse:
    is_reviewer = data.code in config.CODES_REVIEWERS
    is_annotator = data.code in config.CODES_ANNOTATORS

    if not is_reviewer and not is_annotator:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid code",
        )

    user = (
        await session.exec(
            select(User).where(
                User.email == data.email,
                User.first_name == data.first_name,
                User.last_name == data.last_name,
            )
        )
    ).first()

    if not user:
        user = User(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            is_reviewer=is_reviewer,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        user.is_reviewer = is_reviewer
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return LoginResponse(
        id=user.id,  # type: ignore
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_reviewer=user.is_reviewer,
        access_token=data.code,
    )
