"""move native language to users and trim learning spaces

Revision ID: 0004_user_native_and_space_trim
Revises: 0003_learning_space_scope
Create Date: 2026-03-14 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_user_native_and_space_trim"
down_revision = "0003_learning_space_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("native_language", sa.String(length=16), nullable=True))

    op.execute(
        """
        UPDATE users u
        SET native_language = src.native_language
        FROM (
            SELECT DISTINCT ON (user_id) user_id, native_language
            FROM learning_spaces
            WHERE native_language IS NOT NULL
            ORDER BY user_id, updated_at DESC, id DESC
        ) AS src
        WHERE u.id = src.user_id
          AND u.native_language IS NULL
        """
    )

    op.drop_column("learning_spaces", "title")
    op.drop_column("learning_spaces", "native_language")


def downgrade() -> None:
    op.add_column("learning_spaces", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("learning_spaces", sa.Column("native_language", sa.String(length=16), nullable=True))

    op.execute(
        """
        UPDATE learning_spaces ls
        SET native_language = u.native_language
        FROM users u
        WHERE ls.user_id = u.id
          AND ls.native_language IS NULL
        """
    )

    op.drop_column("users", "native_language")
