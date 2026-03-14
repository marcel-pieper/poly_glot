"""add threads messages and translations

Revision ID: 0002_threads_messages_translations
Revises: 0001_initial
Create Date: 2026-03-14 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_threads_messages_translations"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


thread_type_enum = postgresql.ENUM(
    "chat",
    "explain",
    "practice",
    name="thread_type_enum",
    create_type=False,
)
message_role_enum = postgresql.ENUM(
    "user",
    "assistant",
    "system",
    "developer",
    name="message_role_enum",
    create_type=False,
)


def upgrade() -> None:
    thread_type_enum.create(op.get_bind(), checkfirst=True)
    message_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "threads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_thread_id", sa.Integer(), sa.ForeignKey("threads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("type", thread_type_enum, nullable=False),
        sa.Column("seed", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_threads_id", "threads", ["id"], unique=False)
    op.create_index("ix_threads_user_id", "threads", ["user_id"], unique=False)
    op.create_index("ix_threads_parent_thread_id", "threads", ["parent_thread_id"], unique=False)
    op.create_index("ix_threads_type", "threads", ["type"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", message_role_enum, nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_messages_id", "messages", ["id"], unique=False)
    op.create_index("ix_messages_thread_id", "messages", ["thread_id"], unique=False)
    op.create_index("ix_messages_role", "messages", ["role"], unique=False)

    op.create_table(
        "translations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_text", sa.Text(), nullable=False),
        sa.Column("to_text", sa.Text(), nullable=False),
        sa.Column("from_language", sa.String(length=32), nullable=False),
        sa.Column("to_language", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_translations_id", "translations", ["id"], unique=False)
    op.create_index("ix_translations_user_id", "translations", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_translations_user_id", table_name="translations")
    op.drop_index("ix_translations_id", table_name="translations")
    op.drop_table("translations")

    op.drop_index("ix_messages_role", table_name="messages")
    op.drop_index("ix_messages_thread_id", table_name="messages")
    op.drop_index("ix_messages_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_threads_type", table_name="threads")
    op.drop_index("ix_threads_parent_thread_id", table_name="threads")
    op.drop_index("ix_threads_user_id", table_name="threads")
    op.drop_index("ix_threads_id", table_name="threads")
    op.drop_table("threads")

    message_role_enum.drop(op.get_bind(), checkfirst=True)
    thread_type_enum.drop(op.get_bind(), checkfirst=True)
