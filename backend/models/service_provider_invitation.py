from backend.database import db
from datetime import datetime, timezone


class ServiceProviderInvitation(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    service_provider_id = db.Column(
        db.Integer,
        db.ForeignKey("service_provider.id"),
        nullable=False
    )

    organisation_id = db.Column(
        db.Integer,
        db.ForeignKey("organisation.id"),
        nullable=False
    )

    maintenance_request_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_request.id"),
        nullable=True
    )

    token_hash = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending"
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    accepted_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )