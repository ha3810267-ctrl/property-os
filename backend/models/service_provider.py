from backend.database import db
from datetime import datetime, timezone


class ServiceProvider(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    organisation_id = db.Column(
        db.Integer,
        db.ForeignKey("organisation.id"),
        nullable=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    business_name = db.Column(
        db.String(150),
        nullable=True
    )

    email = db.Column(
        db.String(255),
        nullable=False
    )

    phone = db.Column(
        db.String(50),
        nullable=True
    )

    speciality = db.Column(
        db.Text,
        nullable=True
    )

    service_area = db.Column(
        db.String(255),
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True,
        unique=True
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )