from datetime import datetime, timezone

from backend.database import db


class ExternalWorkerCandidate(db.Model):

    __tablename__ = "external_worker_candidate"

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

    # ========================================================
    # CONTRACTOR IDENTITY
    # ========================================================

    provider = db.Column(
        db.String(50),
        nullable=False
    )

    external_id = db.Column(
        db.String(150),
        nullable=False
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    trade = db.Column(
        db.String(100),
        nullable=False
    )

    location = db.Column(
        db.String(150),
        nullable=True
    )

    website = db.Column(
        db.String(500),
        nullable=True
    )

    phone = db.Column(
        db.String(50),
        nullable=True
    )

    email = db.Column(
        db.String(255),
        nullable=True
    )

    source_url = db.Column(
        db.String(500),
        nullable=True
    )

    # ========================================================
    # DISCOVERY INFORMATION
    # ========================================================

    rating = db.Column(
        db.Float,
        nullable=True
    )

    review_count = db.Column(
        db.Integer,
        nullable=True
    )

    availability = db.Column(
        db.String(150),
        nullable=True
    )

    # ========================================================
    # GEMINI MATCHING
    # ========================================================

    match_score = db.Column(
        db.Float,
        nullable=True
    )

    match_reason = db.Column(
        db.Text,
        nullable=True
    )

    ranking_updated_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # ========================================================
    # SELECTION
    # ========================================================

    is_selected = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True
    )

    selected_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )