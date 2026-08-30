from sqlalchemy import Boolean, Column, DateTime, String, Index
from sqlalchemy.sql import func
import uuid6
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    # Primary Key using UUIDv7 (generated via uuid6 for time locality)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7, index=True)
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Audit Timestamps (Timezone Aware)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Soft Deletion
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Partial Unique Index to avoid Soft Delete DB Trap
    __table_args__ = (
        Index(
            'ix_users_email_unique',
            'email',
            unique=True,
            postgresql_where=deleted_at.is_(None)
        ),
    )