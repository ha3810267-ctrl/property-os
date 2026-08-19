from backend.database import db


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    role = db.Column(
        db.String(50),
        nullable=False
    )

    speciality = db.Column(
        db.Text,
        nullable=True
    )

    organisation_id = db.Column(
        db.Integer,
        db.ForeignKey("organisation.id"),
        nullable=False
    )