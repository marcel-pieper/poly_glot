"""add user_vocab table with FSRS scheduling columns

Revision ID: 0007_user_vocab
Revises: 0006_lemmas_and_translations
Create Date: 2026-05-19 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_user_vocab"
down_revision = "0006_lemmas_and_translations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_vocab",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "language_space_id",
            sa.Integer(),
            sa.ForeignKey("language_spaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lemma_id",
            sa.Integer(),
            sa.ForeignKey("lemmas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", sa.SmallInteger(), nullable=False),
        sa.Column("step", sa.SmallInteger(), nullable=True),
        sa.Column("stability", sa.Float(), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.Column("due", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_review", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lapse_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("language_space_id", "lemma_id", name="uq_user_vocab_space_lemma"),
    )
    op.create_index("ix_user_vocab_id", "user_vocab", ["id"], unique=False)
    op.create_index(
        "ix_user_vocab_language_space_id", "user_vocab", ["language_space_id"], unique=False
    )
    op.create_index("ix_user_vocab_lemma_id", "user_vocab", ["lemma_id"], unique=False)
    op.create_index(
        "ix_user_vocab_space_due", "user_vocab", ["language_space_id", "due"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_user_vocab_space_due", table_name="user_vocab")
    op.drop_index("ix_user_vocab_lemma_id", table_name="user_vocab")
    op.drop_index("ix_user_vocab_language_space_id", table_name="user_vocab")
    op.drop_index("ix_user_vocab_id", table_name="user_vocab")
    op.drop_table("user_vocab")
