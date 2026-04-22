"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from api.config import config
from api.db import get_session
from api.models.annotations import User
from api.models.auth import LoginRequest, LoginResponse
from api.services.auth import create_jwt_token

router = APIRouter()


@router.post("/login")
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
                User.full_name == data.full_name,
            )
        )
    ).first()

    if user:
        user.is_reviewer = is_reviewer
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        user = User(
            email=data.email,
            full_name=data.full_name,
            is_reviewer=is_reviewer,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    access_token = await create_jwt_token(user)

    return LoginResponse(
        id=user.id,  # type: ignore
        email=user.email,
        full_name=user.full_name,
        is_reviewer=user.is_reviewer,
        access_token=access_token,
    )
