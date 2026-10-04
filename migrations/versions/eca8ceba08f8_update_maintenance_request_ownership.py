"""update maintenance request ownership

Revision ID: eca8ceba08f8
Revises: 04c17a36bda2
Create Date: 2026-10-04 10:32:12.440972
"""

from alembic import op
import sqlalchemy as sa


revision = "eca8ceba08f8"
down_revision = "04c17a36bda2"
branch_labels = None
depends_on = None


def upgrade():
    # Remove data belonging to the old maintenance workflow.
    op.execute("DELETE FROM external_worker_message")
    op.execute("DELETE FROM external_worker_candidate")
    op.execute("DELETE FROM task_assignment")
    op.execute("DELETE FROM maintenance_request")

    with op.batch_alter_table("maintenance_request", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("user_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("location", sa.String(length=500), nullable=True)
        )

        batch_op.drop_constraint(
            batch_op.f("maintenance_request_tenant_id_fkey"),
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            batch_op.f("maintenance_request_assigned_to_fkey"),
            type_="foreignkey",
        )

        batch_op.create_foreign_key(
            "maintenance_request_user_id_fkey",
            "user",
            ["user_id"],
            ["id"],
        )

        batch_op.drop_column("assigned_to")
        batch_op.drop_column("tenant_id")

    with op.batch_alter_table("maintenance_request", schema=None) as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            "location",
            existing_type=sa.String(length=500),
            nullable=False,
        )


def downgrade():
    with op.batch_alter_table("maintenance_request", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "tenant_id",
                sa.INTEGER(),
                autoincrement=False,
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "assigned_to",
                sa.INTEGER(),
                autoincrement=False,
                nullable=True,
            )
        )

        batch_op.drop_constraint(
            "maintenance_request_user_id_fkey",
            type_="foreignkey",
        )

        batch_op.create_foreign_key(
            batch_op.f("maintenance_request_assigned_to_fkey"),
            "user",
            ["assigned_to"],
            ["id"],
        )
        batch_op.create_foreign_key(
            batch_op.f("maintenance_request_tenant_id_fkey"),
            "tenant",
            ["tenant_id"],
            ["id"],
        )

        batch_op.drop_column("location")
        batch_op.drop_column("user_id")