from backend.database import db
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint


class TaskAssignment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    maintenance_request_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_request.id"),
        nullable=False,
        index=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True
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

    __table_args__ = (
        CheckConstraint(
            "assignment_method IN ('manual', 'ai')",
            name="check_assignment_method"
        ),
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 1)",
            name="check_assignment_score"
        ),
    )