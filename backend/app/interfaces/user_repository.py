from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class IUserRepository(ABC):
    @abstractmethod
    async def get(self, id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[User]:
        pass

    @abstractmethod
    async def create(self, obj_in: UserCreate) -> User:
        pass

    @abstractmethod
    async def update(self, db_obj: User, obj_in: UserUpdate) -> User:
        pass

    @abstractmethod
    async def remove(self, id: UUID) -> User:
        pass

    @abstractmethod
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        pass
