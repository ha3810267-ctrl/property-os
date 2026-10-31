"""add reply token

Revision ID: 6c6d98a2fad2
Revises: ead01f41f97d
"""

from alembic import op
import sqlalchemy as sa


revision = "6c6d98a2fad2"
down_revision = "ead01f41f97d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "external_worker_message",
        sa.Column("reply_token", sa.String(length=100), nullable=True)
    )

    op.create_unique_constraint(
        "uq_external_worker_message_reply_token",
        "external_worker_message",
        ["reply_token"]
    )


def downgrade():
    op.drop_constraint(
        "uq_external_worker_message_reply_token",
        "external_worker_message",
        type_="unique"
    )

    op.drop_column(
        "external_worker_message",
        "reply_token"
    )