from backend.database import db
from datetime import datetime, timezone
class TaskAssignment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    maintenance_request_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_request.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    assigned_at = db.Column(
    db.DateTime,
    nullable=False,
    default=lambda: datetime.now(timezone.utc)
)

    assignment_method = db.Column(
        db.String(30),
        nullable=False
    )

    score = db.Column(
        db.Float,
        nullable=True
    )