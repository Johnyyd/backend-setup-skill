from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=False,
    # LỖ HỔNG ĐƯỢC VÁ: Từ bỏ quyền làm Pool của SQLAlchemy để chống rác kết nối đè lên PgBouncer
    poolclass=NullPool,
    # LỖ HỔNG ĐƯỢC VÁ: Vô hiệu hóa prepared statement cache của asyncpg khi dùng với PgBouncer Transaction Pool
    connect_args={"prepared_statement_cache_size": 0}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()