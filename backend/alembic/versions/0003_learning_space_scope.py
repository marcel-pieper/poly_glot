"""scope thread data by learning space

Revision ID: 0003_learning_space_scope
Revises: 0002_threads_messages_translations
Create Date: 2026-03-14 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_learning_space_scope"
down_revision = "0002_threads_messages_translations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_spaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("target_language", sa.String(length=16), nullable=False),
        sa.Column("native_language", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "target_language", name="uq_learning_spaces_user_language"),
    )
    op.create_index("ix_learning_spaces_id", "learning_spaces", ["id"], unique=False)
    op.create_index("ix_learning_spaces_user_id", "learning_spaces", ["user_id"], unique=False)
    op.create_index("ix_learning_spaces_target_language", "learning_spaces", ["target_language"], unique=False)

    op.add_column("threads", sa.Column("learning_space_id", sa.Integer(), nullable=True))
    op.add_column("translations", sa.Column("learning_space_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_threads_learning_space_id",
        "threads",
        "learning_spaces",
        ["learning_space_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_translations_learning_space_id",
        "translations",
        "learning_spaces",
        ["learning_space_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_threads_learning_space_id", "threads", ["learning_space_id"], unique=False)
    op.create_index("ix_translations_learning_space_id", "translations", ["learning_space_id"], unique=False)

    op.execute(
        """
        INSERT INTO learning_spaces (user_id, target_language, created_at, updated_at)
        SELECT DISTINCT user_id, 'und', now(), now()
        FROM (
            SELECT user_id FROM threads
            UNION
            SELECT user_id FROM translations
        ) AS scoped_users
        WHERE user_id IS NOT NULL
        ON CONFLICT (user_id, target_language) DO NOTHING
        """
    )

    op.execute(
        """
        UPDATE threads t
        SET learning_space_id = ls.id
        FROM learning_spaces ls
        WHERE t.user_id = ls.user_id
          AND ls.target_language = 'und'
          AND t.learning_space_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE translations tr
        SET learning_space_id = ls.id
        FROM learning_spaces ls
        WHERE tr.user_id = ls.user_id
          AND ls.target_language = 'und'
          AND tr.learning_space_id IS NULL
        """
    )

    op.alter_column("threads", "learning_space_id", nullable=False)
    op.alter_column("translations", "learning_space_id", nullable=False)

    op.drop_index("ix_threads_user_id", table_name="threads")
    op.drop_index("ix_translations_user_id", table_name="translations")
    op.drop_column("threads", "user_id")
    op.drop_column("translations", "user_id")


def downgrade() -> None:
    op.add_column("threads", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("translations", sa.Column("user_id", sa.Integer(), nullable=True))

    op.execute(
        """
        UPDATE threads t
        SET user_id = ls.user_id
        FROM learning_spaces ls
        WHERE t.learning_space_id = ls.id
        """
    )
    op.execute(
        """
        UPDATE translations tr
        SET user_id = ls.user_id
        FROM learning_spaces ls
        WHERE tr.learning_space_id = ls.id
        """
    )

    op.alter_column("threads", "user_id", nullable=False)
    op.alter_column("translations", "user_id", nullable=False)

    op.create_foreign_key(
        "threads_user_id_fkey",
        "threads",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "translations_user_id_fkey",
        "translations",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_threads_user_id", "threads", ["user_id"], unique=False)
    op.create_index("ix_translations_user_id", "translations", ["user_id"], unique=False)

    op.drop_index("ix_translations_learning_space_id", table_name="translations")
    op.drop_index("ix_threads_learning_space_id", table_name="threads")
    op.drop_constraint("fk_translations_learning_space_id", "translations", type_="foreignkey")
    op.drop_constraint("fk_threads_learning_space_id", "threads", type_="foreignkey")
    op.drop_column("translations", "learning_space_id")
    op.drop_column("threads", "learning_space_id")

    op.drop_index("ix_learning_spaces_target_language", table_name="learning_spaces")
    op.drop_index("ix_learning_spaces_user_id", table_name="learning_spaces")
    op.drop_index("ix_learning_spaces_id", table_name="learning_spaces")
    op.drop_table("learning_spaces")
