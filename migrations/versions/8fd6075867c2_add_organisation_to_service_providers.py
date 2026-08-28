"""add organisation to service providers

Revision ID: 8fd6075867c2
Revises: e937a57c9e80
Create Date: 2026-08-24 12:40:55.311996

"""

from alembic import op
import sqlalchemy as sa


revision = "8fd6075867c2"
down_revision = "e937a57c9e80"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table(
        "service_provider",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "organisation_id",
                sa.Integer(),
                nullable=True
            )
        )

        batch_op.create_foreign_key(
            "fk_service_provider_organisation_id",
            "organisation",
            ["organisation_id"],
            ["id"]
        )


def downgrade():
    with op.batch_alter_table(
        "service_provider",
        schema=None
    ) as batch_op:

        batch_op.drop_constraint(
            "fk_service_provider_organisation_id",
            type_="foreignkey"
        )

        batch_op.drop_column(
            "organisation_id"
        )