from datetime import datetime, timezone

from backend.database import db


class ExternalWorkerMessage(db.Model):

    __tablename__ = "external_worker_message"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    maintenance_request_id = db.Column(
        db.Integer,
        db.ForeignKey("maintenance_request.id"),
        nullable=False,
        index=True
    )

    candidate_id = db.Column(
        db.Integer,
        db.ForeignKey("external_worker_candidate.id"),
        nullable=False,
        index=True
    )

    # ========================================================
    # MESSAGE DIRECTION
    # ========================================================

    direction = db.Column(
        db.String(20),
        nullable=False
    )

    # outbound = PropertyOS → contractor
    # inbound = contractor → PropertyOS

    # ========================================================
    # EMAIL IDENTIFICATION
    # ========================================================

    resend_message_id = db.Column(
        db.String(255),
        nullable=True,
        index=True
    )

    in_reply_to = db.Column(
        db.String(255),
        nullable=True,
        index=True
    )

    message_id = db.Column(
        db.String(500),
        nullable=True,
        index=True
    )

    # ========================================================
    # EMAIL ADDRESSES
    # ========================================================

    sender_email = db.Column(
        db.String(255),
        nullable=True
    )

    recipient_email = db.Column(
        db.String(255),
        nullable=True
    )

    # ========================================================
    # RAW MESSAGE CONTENT
    # ========================================================

    subject = db.Column(
        db.Text,
        nullable=True
    )

    text_body = db.Column(
        db.Text,
        nullable=True
    )

    html_body = db.Column(
        db.Text,
        nullable=True
    )

    raw_payload = db.Column(
        db.Text,
        nullable=True
    )

    # ========================================================
    # TIMESTAMP
    # ========================================================

    received_at = db.Column(
        db.DateTime,
        nullable=True
    )

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