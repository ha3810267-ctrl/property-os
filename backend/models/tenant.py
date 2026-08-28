from backend.database import db


class Tenant(db.Model):

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

    property_id = db.Column(
        db.Integer,
        db.ForeignKey("property.id"),
        nullable=False
    )