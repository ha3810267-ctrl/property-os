from backend.database import db

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    organisation_id = db.Column(
    db.Integer,
    db.ForeignKey("organisation.id"),
    nullable=False
)