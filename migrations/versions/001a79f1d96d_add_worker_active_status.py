"""add worker active status

Revision ID: 001a79f1d96d
Revises: 8857f6a8d3f2
Create Date: 2026-08-23 00:17:54.975080

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001a79f1d96d'
down_revision = '8857f6a8d3f2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'is_active',
                sa.Boolean(),
                nullable=False,
                server_default=sa.true()
            )
        )


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_active')