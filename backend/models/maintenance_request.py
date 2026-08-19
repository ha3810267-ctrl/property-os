from backend.database import db
from datetime import datetime, timezone


class MaintenanceRequest(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    tenant_id = db.Column(
        db.Integer,
        db.ForeignKey("tenant.id"),
        nullable=False
    )

    assigned_to = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="open"
    )

    priority = db.Column(
        db.String(30),
        nullable=False,
        default="normal"
    )

    category = db.Column(
        db.String(100),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )