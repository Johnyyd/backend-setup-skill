import pytest
import pytest_asyncio
import asyncio
from sqlalchemy import event, NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from httpx import AsyncClient, ASGITransport
from app.db.session import get_db
from app.main import app
from app.core.config import settings

# Using the actual postgres DB since sqlite cannot handle asyncpg.
# For a real pipeline, we'd spawn a test db, but for here we use the configured db url.
TEST_DB_URL = str(settings.SQLALCHEMY_DATABASE_URI)
engine = create_async_engine(
    TEST_DB_URL, 
    echo=False,
    poolclass=NullPool,
    connect_args={"prepared_statement_cache_size": 0}
)

@pytest.fixture(scope="session")
def event_loop():
    """Force all test cases to share the same Async Event Loop to prevent SQLAlchemy crashes."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a Savepoint (Nested Transaction) for each test and rollback after completion."""
    from app.db.base_class import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.connect() as connection:
        transaction = await connection.begin()
        async_session = AsyncSession(bind=connection, expire_on_commit=False)

        await connection.begin_nested()

        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def end_savepoint(session, transaction):
            if transaction.nested and not transaction._parent.nested:
                connection.sync_connection.begin_nested()

        yield async_session

        await async_session.close()
        await transaction.rollback()

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Override FastAPI's Dependency Injection to force the API to use the test's Savepoint."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_db, None)
