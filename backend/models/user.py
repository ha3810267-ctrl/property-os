from backend.database import db


class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    password_reset_token_hash = db.Column(
        db.String(255),
        nullable=True
    )

    password_reset_expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    role = db.Column(
        db.String(50),
        nullable=False
    )

    speciality = db.Column(
        db.Text,
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    organisation_id = db.Column(
        db.Integer,
        db.ForeignKey("organisation.id"),
        nullable=False
    )

    tenant_id = db.Column(
        db.Integer,
        db.ForeignKey("tenant.id"),
        nullable=True
    )