from backend.database import db
from datetime import datetime, timezone


class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    description = db.Column(
        db.String(1000),
        nullable=False
    )

    tenant_id = db.Column(
        db.Integer,
        db.ForeignKey("tenant.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="open"
    )