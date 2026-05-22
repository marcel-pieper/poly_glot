from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, inspect, pool, text

from app.core.config import get_settings
from app.db.base import Base
from app.models import (  # noqa: F401
    EmailVerificationCode,
    LanguageSpace,
    Lemma,
    LemmaTranslation,
    Message,
    SupportedLanguage,
    Thread,
    Translation,
    User,
    UserVocab,
)

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DEFAULT_VERSION_NUM_LENGTH = 128


def version_num_length() -> int:
    """See version_num_length in alembic.ini (Alembic defaults to VARCHAR(32))."""
    raw = config.get_main_option("version_num_length")
    if raw is None:
        return DEFAULT_VERSION_NUM_LENGTH
    return int(raw)


def ensure_alembic_version_column(connection, length: int) -> None:
    """
    Widen alembic_version.version_num so long revision ids (e.g. 0002_threads_messages_translations) fit.
    Alembic creates the table with VARCHAR(32); this runs before each online migration.
    """
    insp = inspect(connection)
    if "alembic_version" not in insp.get_table_names():
        return
    connection.execute(
        text(f"ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR({length})")
    )
    connection.commit()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        ensure_alembic_version_column(connection, version_num_length())
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
