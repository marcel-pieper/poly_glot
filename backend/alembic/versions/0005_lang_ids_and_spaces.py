"""add supported languages and id-based language scoping

Revision ID: 0005_lang_ids_and_spaces
Revises: 0004_user_native_and_space_trim
Create Date: 2026-03-14 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_lang_ids_and_spaces"
down_revision = "0004_user_native_and_space_trim"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supported_languages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("native_name", sa.String(length=100), nullable=True),
        sa.Column("learning_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("code", name="uq_supported_languages_code"),
    )
    op.create_index("ix_supported_languages_id", "supported_languages", ["id"], unique=False)
    op.create_index("ix_supported_languages_code", "supported_languages", ["code"], unique=False)

    op.execute(
        """
        INSERT INTO supported_languages (code, name, native_name, learning_enabled)
        VALUES
          ('und', 'Undetermined', 'Undetermined', false),
          ('en', 'English', 'English', true),
          ('es', 'Spanish', 'Español', true),
          ('fr', 'French', 'Français', true),
          ('de', 'German', 'Deutsch', true),
          ('it', 'Italian', 'Italiano', true),
          ('pt', 'Portuguese', 'Português', true),
          ('nl', 'Dutch', 'Nederlands', true),
          ('ru', 'Russian', 'Русский', true),
          ('ja', 'Japanese', '日本語', true),
          ('ko', 'Korean', '한국어', true),
          ('zh', 'Chinese', '中文', true)
        ON CONFLICT (code) DO NOTHING
        """
    )

    # learning_spaces -> language_spaces
    op.rename_table("learning_spaces", "language_spaces")
    op.execute("ALTER INDEX ix_learning_spaces_id RENAME TO ix_language_spaces_id")
    op.execute("ALTER INDEX ix_learning_spaces_user_id RENAME TO ix_language_spaces_user_id")
    op.execute("ALTER INDEX ix_learning_spaces_target_language RENAME TO ix_language_spaces_target_language")

    # learning_space_id -> language_space_id
    op.alter_column("threads", "learning_space_id", new_column_name="language_space_id")
    op.alter_column("translations", "learning_space_id", new_column_name="language_space_id")
    op.execute("ALTER INDEX ix_threads_learning_space_id RENAME TO ix_threads_language_space_id")
    op.execute("ALTER INDEX ix_translations_learning_space_id RENAME TO ix_translations_language_space_id")

    # language_spaces.target_language (string) -> target_language_id (FK)
    op.add_column("language_spaces", sa.Column("target_language_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE language_spaces ls
        SET target_language_id = sl.id
        FROM supported_languages sl
        WHERE sl.code = ls.target_language
        """
    )
    op.execute(
        """
        UPDATE language_spaces
        SET target_language_id = (SELECT id FROM supported_languages WHERE code = 'und')
        WHERE target_language_id IS NULL
        """
    )
    op.alter_column("language_spaces", "target_language_id", nullable=False)
    op.create_foreign_key(
        "fk_language_spaces_target_language_id",
        "language_spaces",
        "supported_languages",
        ["target_language_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_language_spaces_target_language_id", "language_spaces", ["target_language_id"], unique=False)
    op.drop_constraint("uq_learning_spaces_user_language", "language_spaces", type_="unique")
    op.create_unique_constraint(
        "uq_language_spaces_user_target_language",
        "language_spaces",
        ["user_id", "target_language_id"],
    )
    op.drop_index("ix_language_spaces_target_language", table_name="language_spaces")
    op.drop_column("language_spaces", "target_language")

    # users.native_language (string) -> native_language_id (FK) and active_language_space_id
    op.add_column("users", sa.Column("native_language_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("active_language_space_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE users u
        SET native_language_id = sl.id
        FROM supported_languages sl
        WHERE sl.code = u.native_language
        """
    )
    op.execute(
        """
        UPDATE users u
        SET active_language_space_id = ls.id
        FROM (
            SELECT DISTINCT ON (user_id) id, user_id
            FROM language_spaces
            ORDER BY user_id, updated_at DESC, id DESC
        ) AS ls
        WHERE u.id = ls.user_id
        """
    )
    op.create_foreign_key(
        "fk_users_native_language_id",
        "users",
        "supported_languages",
        ["native_language_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_users_active_language_space_id",
        "users",
        "language_spaces",
        ["active_language_space_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_users_native_language_id", "users", ["native_language_id"], unique=False)
    op.create_index("ix_users_active_language_space_id", "users", ["active_language_space_id"], unique=False)
    op.drop_column("users", "native_language")


def downgrade() -> None:
    op.add_column("users", sa.Column("native_language", sa.String(length=16), nullable=True))
    op.execute(
        """
        UPDATE users u
        SET native_language = sl.code
        FROM supported_languages sl
        WHERE u.native_language_id = sl.id
        """
    )
    op.drop_index("ix_users_active_language_space_id", table_name="users")
    op.drop_index("ix_users_native_language_id", table_name="users")
    op.drop_constraint("fk_users_active_language_space_id", "users", type_="foreignkey")
    op.drop_constraint("fk_users_native_language_id", "users", type_="foreignkey")
    op.drop_column("users", "active_language_space_id")
    op.drop_column("users", "native_language_id")

    op.add_column("language_spaces", sa.Column("target_language", sa.String(length=16), nullable=True))
    op.execute(
        """
        UPDATE language_spaces ls
        SET target_language = sl.code
        FROM supported_languages sl
        WHERE ls.target_language_id = sl.id
        """
    )
    op.alter_column("language_spaces", "target_language", nullable=False)
    op.create_index("ix_language_spaces_target_language", "language_spaces", ["target_language"], unique=False)
    op.drop_constraint("uq_language_spaces_user_target_language", "language_spaces", type_="unique")
    op.create_unique_constraint("uq_learning_spaces_user_language", "language_spaces", ["user_id", "target_language"])
    op.drop_index("ix_language_spaces_target_language_id", table_name="language_spaces")
    op.drop_constraint("fk_language_spaces_target_language_id", "language_spaces", type_="foreignkey")
    op.drop_column("language_spaces", "target_language_id")

    op.alter_column("threads", "language_space_id", new_column_name="learning_space_id")
    op.alter_column("translations", "language_space_id", new_column_name="learning_space_id")
    op.execute("ALTER INDEX ix_threads_language_space_id RENAME TO ix_threads_learning_space_id")
    op.execute("ALTER INDEX ix_translations_language_space_id RENAME TO ix_translations_learning_space_id")

    op.execute("ALTER INDEX ix_language_spaces_target_language RENAME TO ix_learning_spaces_target_language")
    op.execute("ALTER INDEX ix_language_spaces_user_id RENAME TO ix_learning_spaces_user_id")
    op.execute("ALTER INDEX ix_language_spaces_id RENAME TO ix_learning_spaces_id")
    op.rename_table("language_spaces", "learning_spaces")

    op.drop_index("ix_supported_languages_code", table_name="supported_languages")
    op.drop_index("ix_supported_languages_id", table_name="supported_languages")
    op.drop_table("supported_languages")
