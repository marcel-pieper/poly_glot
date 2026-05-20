"""add lemmas and lemma_translations tables

Revision ID: 0006_lemmas_and_translations
Revises: 0005_lang_ids_and_spaces
Create Date: 2026-05-19 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_lemmas_and_translations"
down_revision = "0005_lang_ids_and_spaces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lemmas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("lemma", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("language", "lemma", "type", name="uq_lemmas_language_lemma_type"),
    )
    op.create_index("ix_lemmas_id", "lemmas", ["id"], unique=False)
    op.create_index("ix_lemmas_language", "lemmas", ["language"], unique=False)
    op.create_index("ix_lemmas_lemma", "lemmas", ["lemma"], unique=False)

    op.create_table(
        "lemma_translations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "lemma_id",
            sa.Integer(),
            sa.ForeignKey("lemmas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("gloss_language", sa.String(length=32), nullable=False),
        sa.Column("translation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "lemma_id",
            "gloss_language",
            "translation",
            name="uq_lemma_translations_lemma_gloss_translation",
        ),
    )
    op.create_index("ix_lemma_translations_id", "lemma_translations", ["id"], unique=False)
    op.create_index("ix_lemma_translations_lemma_id", "lemma_translations", ["lemma_id"], unique=False)
    op.create_index(
        "ix_lemma_translations_gloss_language", "lemma_translations", ["gloss_language"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_lemma_translations_gloss_language", table_name="lemma_translations")
    op.drop_index("ix_lemma_translations_lemma_id", table_name="lemma_translations")
    op.drop_index("ix_lemma_translations_id", table_name="lemma_translations")
    op.drop_table("lemma_translations")

    op.drop_index("ix_lemmas_lemma", table_name="lemmas")
    op.drop_index("ix_lemmas_language", table_name="lemmas")
    op.drop_index("ix_lemmas_id", table_name="lemmas")
    op.drop_table("lemmas")
