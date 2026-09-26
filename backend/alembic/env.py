import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool, text, Table, MetaData, Column, String, PrimaryKeyConstraint
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from alembic.ddl.impl import DefaultImpl

# Override DefaultImpl.version_table_impl to support longer revision names (e.g. 0007_neon_single_store_architecture)
def _custom_version_table_impl(self, *, version_table: str, version_table_schema: str | None, version_table_pk: bool, **kw):
    vt = Table(
        version_table,
        MetaData(),
        Column("version_num", String(64), nullable=False),
        schema=version_table_schema,
    )
    if version_table_pk:
        vt.append_constraint(PrimaryKeyConstraint("version_num", name=f"{version_table}_pkc"))
    return vt

DefaultImpl.version_table_impl = _custom_version_table_impl

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.core.database import Base, normalize_database_url
import app.db.models  # Ensure all models are registered

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    x_args = context.get_x_argument(as_dictionary=True)
    if "db_url" in x_args:
        return normalize_database_url(x_args["db_url"])
    main_url = config.get_main_option("sqlalchemy.url")
    if main_url and "driver://user:pass@localhost/dbname" not in main_url:
        return normalize_database_url(main_url)
    raw = os.getenv("DATABASE_URL", settings.database_url)
    return normalize_database_url(raw)


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


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        },
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
