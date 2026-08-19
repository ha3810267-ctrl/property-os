from backend.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    organisation_id = db.Column(
        db.Integer,
        db.ForeignKey("organisation.id"),
        nullable=False
    )