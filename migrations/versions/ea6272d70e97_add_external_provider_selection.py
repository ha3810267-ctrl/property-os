"""add external provider selection

Revision ID: ea6272d70e97
Revises: 655d8ea4eed0
Create Date: 2026-08-24 21:42:08.488018
"""

from alembic import op
import sqlalchemy as sa


revision = "ea6272d70e97"
down_revision = "655d8ea4eed0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "external_worker_candidate",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "is_selected",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )

        batch_op.add_column(
            sa.Column(
                "selected_at",
                sa.DateTime(),
                nullable=True
            )
        )

        batch_op.alter_column(
            "is_selected",
            server_default=None
        )


def downgrade():
    with op.batch_alter_table(
        "external_worker_candidate",
        schema=None
    ) as batch_op:

        batch_op.drop_column("selected_at")
        batch_op.drop_column("is_selected")