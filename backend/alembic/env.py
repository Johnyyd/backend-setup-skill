import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Add the app directory to the path so we can import our models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.db.base_class import Base
from app import models  # noqa

target_metadata = Base.metadata


def get_url():
    if os.getenv("GENERATE_MIGRATION"):
        return "sqlite+aiosqlite:///:memory:"
    # LỖ HỔNG ĐƯỢC VÁ: Ưu tiên dùng SYNC_DATABASE_URL (nối thẳng DB) khi chạy local migration để không làm sập PgBouncer
    if os.getenv("SYNC_DATABASE_URL"):
        return os.getenv("SYNC_DATABASE_URL")
    from app.core.config import settings
    return str(settings.SQLALCHEMY_DATABASE_URI)


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()