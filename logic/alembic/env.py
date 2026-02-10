from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

# Add parent directory to sys.path to find the 'app' module.
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.database import Base, DATABASE_URL, engine

from alembic import context

config = context.config

# Set the sqlalchemy.url from our database module
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Import all models so Alembic can detect them for autogenerate
from app import models  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
