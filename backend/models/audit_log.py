from datetime import datetime, timezone

from backend.database import db


class AuditLog(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    organisation_id = db.Column(
        db.Integer,
        db.ForeignKey("organisation.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    resource_type = db.Column(
        db.String(100),
        nullable=False
    )

    resource_id = db.Column(
        db.Integer,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )