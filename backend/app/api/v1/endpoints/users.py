from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app import schemas
from app.interfaces.user_repository import IUserRepository
from app.api.v1.responses.standard import StandardResponse

router = APIRouter()


@router.post("/", response_model=StandardResponse[schemas.User], status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: schemas.UserCreate,
    user_repo: IUserRepository = Depends()
):
    """
    Create a new user.
    """
    user = await user_repo.get_by_email(email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = await user_repo.create(obj_in=user_in)
    return StandardResponse(success=True, data=user)


@router.get("/", response_model=StandardResponse[List[schemas.User]])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    user_repo: IUserRepository = Depends()
):
    """
    Retrieve users.
    """
    users = await user_repo.get_multi(skip=skip, limit=limit)
    return StandardResponse(success=True, data=users)


@router.get("/{user_id}", response_model=StandardResponse[schemas.User])
async def read_user_by_id(
    user_id: UUID,
    user_repo: IUserRepository = Depends()
):
    """
    Get a specific user by id.
    """
    user = await user_repo.get(id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    return StandardResponse(success=True, data=user)