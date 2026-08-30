from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app import schemas
from app.utils import security
from app.core.config import settings
from app.interfaces.user_repository import IUserRepository
from app.api.v1.responses.standard import StandardResponse

router = APIRouter()


@router.post("/login/access-token", response_model=StandardResponse[schemas.Token])
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: IUserRepository = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await user_repo.authenticate(
        email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "access_token": security.create_access_token(
            {"sub": str(user.id)}, expires_delta=access_token_expires
        ),
        "refresh_token": security.create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
    }
    return StandardResponse(success=True, data=token_data)


@router.post("/login/refresh-token", response_model=StandardResponse[schemas.Token])
async def refresh_token(
    refresh_token: str,
    user_repo: IUserRepository = Depends()
):
    """
    Refresh access token using refresh token
    """
    payload = security.decode_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    import uuid
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repo.get(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "access_token": security.create_access_token(
            {"sub": str(user.id)}, expires_delta=access_token_expires
        ),
        "refresh_token": security.create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
    }
    return StandardResponse(success=True, data=token_data)