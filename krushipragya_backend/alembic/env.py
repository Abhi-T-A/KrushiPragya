from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.database.base import Base
import app.models
from app.database.connection import normalize_database_url
from sqlalchemy import Table, Column
from sqlalchemy.dialects.postgresql import UUID

# Register external Supabase auth.users stub so SQLAlchemy can resolve foreign keys during autogenerate
if "auth.users" not in Base.metadata.tables:
    Table("users", Base.metadata, Column("id", UUID(as_uuid=True), primary_key=True), schema="auth")

# Unmanaged baseline tables to ignore during autogenerate comparisons
UNMANAGED_BASELINE_TABLES = {
    "weather_seed",
    "disease_risk_kb",
    "models",
    "model_metrics",
    "datasets",
    "dataset_images",
}


def include_object(object, name, type_, reflected, compare_to):
    """Filter out Supabase auth schema and unmanaged baseline tables from autogenerate."""
    # Ignore any objects belonging to the external 'auth' schema
    if hasattr(object, "schema") and object.schema == "auth":
        return False

    # Ignore pre-existing unmanaged baseline tables and their constraints/indexes
    if type_ == "table":
        if name in UNMANAGED_BASELINE_TABLES:
            return False
    elif type_ in ("index", "unique_constraint", "foreign_key_constraint", "check_constraint"):
        table = getattr(object, "table", None)
        if table is not None and table.name in UNMANAGED_BASELINE_TABLES:
            return False

    return True


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata


def get_url() -> str:
    """Get normalized database URL from application settings (prefers DIRECT_URL for migrations)."""
    raw_url = settings.DIRECT_URL or settings.DATABASE_URL
    if not raw_url or not raw_url.strip():
        return ""
    return normalize_database_url(raw_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    """
    url = get_url()
    if not url:
        raise ValueError(
            "DATABASE_URL is not set. Please define DATABASE_URL in your .env or environment variables."
        )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    url = get_url()
    if not url:
        raise ValueError(
            "DATABASE_URL is not set. Please define DATABASE_URL in your .env or environment variables."
        )

    # Override sqlalchemy.url with application settings
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
