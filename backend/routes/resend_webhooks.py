
import json
import os
from datetime import datetime, timezone

import resend
from svix.webhooks import Webhook

from flask import Blueprint, jsonify, request

from backend.database import db
from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)
from backend.models.external_worker_message import (
    ExternalWorkerMessage
)


resend_webhooks_bp = Blueprint(
    "resend_webhooks",
    __name__,
    url_prefix="/webhooks/resend"
)


RESEND_API_KEY = os.getenv("RESEND_API_KEY")

RESEND_WEBHOOK_SECRET = os.getenv(
    "RESEND_WEBHOOK_SECRET"
)


@resend_webhooks_bp.route(
    "/inbound",
    methods=["POST"]
)
def inbound_email():

    # ========================================================
    # RAW WEBHOOK BODY
    # ========================================================

    raw_body = request.get_data(
        as_text=True
    )

    if not raw_body:
        return jsonify({
            "error": "Empty webhook body"
        }), 400

    # ========================================================
    # WEBHOOK SIGNATURE HEADERS
    # ========================================================

    svix_id = request.headers.get(
        "svix-id"
    )

    svix_timestamp = request.headers.get(
        "svix-timestamp"
    )

    svix_signature = request.headers.get(
        "svix-signature"
    )

    if (
        not svix_id
        or not svix_timestamp
        or not svix_signature
    ):
        return jsonify({
            "error": "Missing webhook signature headers"
        }), 400

    if not RESEND_WEBHOOK_SECRET:
        return jsonify({
            "error": "RESEND_WEBHOOK_SECRET is not configured"
        }), 500

    # ========================================================
    # VERIFY RESEND / SVIX WEBHOOK
    # ========================================================

    try:

        webhook = Webhook(
            RESEND_WEBHOOK_SECRET
        )

        event = webhook.verify(
            raw_body,
            {
                "svix-id": svix_id,
                "svix-timestamp": svix_timestamp,
                "svix-signature": svix_signature
            }
        )

    except Exception as exc:

        print(
            "RESEND WEBHOOK VERIFICATION ERROR:",
            repr(exc)
        )

        return jsonify({
            "error": "Invalid webhook signature"
        }), 400

    # ========================================================
    # EVENT TYPE
    # ========================================================

    if event.get("type") != "email.received":
        return jsonify({
            "status": "ignored"
        }), 200

    data = event.get(
        "data"
    ) or {}

    resend_email_id = data.get(
        "email_id"
    )

    message_id = data.get(
        "message_id"
    )

    if not resend_email_id:
        return jsonify({
            "error": "Missing email_id"
        }), 400

    # ========================================================
    # IDEMPOTENCY
    # ========================================================

    existing_message = (
        ExternalWorkerMessage.query
        .filter_by(
            resend_message_id=resend_email_id
        )
        .first()
    )

    if existing_message:
        return jsonify({
            "status": "already_processed"
        }), 200

    # ========================================================
    # RESEND API
    # ========================================================

    if not RESEND_API_KEY:
        return jsonify({
            "error": "RESEND_API_KEY is not configured"
        }), 500

    resend.api_key = RESEND_API_KEY

    # ========================================================
    # RETRIEVE FULL RECEIVED EMAIL
    # ========================================================

    try:

        received_email = (
            resend.Emails.Receiving.get(
                resend_email_id
            )
        )

    except Exception as exc:

        print(
            "RESEND RECEIVED EMAIL ERROR:",
            repr(exc)
        )

        return jsonify({
            "error": "Failed to retrieve received email"
        }), 500

    if isinstance(
        received_email,
        dict
    ):

        email_data = (
            received_email.get("data")
            or received_email
        )

    else:

        email_data = getattr(
            received_email,
            "data",
            received_email
        )

    def get_value(
        name,
        default=None
    ):

        if isinstance(
            email_data,
            dict
        ):

            return email_data.get(
                name,
                default
            )

        return getattr(
            email_data,
            name,
            default
        )

    sender_email = get_value(
        "from"
    )

    recipient_emails = get_value(
        "to"
    ) or []

    subject = get_value(
        "subject"
    )

    text_body = get_value(
        "text"
    )

    html_body = get_value(
        "html"
    )

    retrieved_message_id = get_value(
        "message_id"
    )

    if not message_id:
        message_id = retrieved_message_id

    if isinstance(
        recipient_emails,
        str
    ):

        recipient_emails = [
            recipient_emails
        ]

    recipient_email = (
        recipient_emails[0]
        if recipient_emails
        else None
    )

    # ========================================================
    # RAW PAYLOAD
    # ========================================================

    raw_payload = json.dumps(
        event,
        ensure_ascii=False
    )

    # ========================================================
    # NORMALISE SENDER ADDRESS
    # ========================================================

    sender_address = sender_email

    if (
        sender_email
        and "<" in sender_email
        and ">" in sender_email
    ):

        sender_address = (
            sender_email
            .split("<", 1)[1]
            .split(">", 1)[0]
            .strip()
        )

    if sender_address:

        sender_address = (
            sender_address
            .lower()
            .strip()
        )

    # ========================================================
    # FIND CONTRACTOR
    # ========================================================

    candidate = None

    if sender_address:

        candidate = (
            ExternalWorkerCandidate.query
            .filter(
                ExternalWorkerCandidate.email
                == sender_address
            )
            .order_by(
                ExternalWorkerCandidate.created_at.desc()
            )
            .first()
        )

    # ========================================================
    # UNMATCHED EMAIL
    # ========================================================

    if not candidate:

        return jsonify({
            "status": "received",
            "matched": False
        }), 200

    # ========================================================
    # SAVE INBOUND MESSAGE
    # ========================================================

    message = ExternalWorkerMessage(
        maintenance_request_id=(
            candidate.maintenance_request_id
        ),
        candidate_id=candidate.id,
        direction="inbound",
        resend_message_id=resend_email_id,
        message_id=message_id,
        sender_email=sender_email,
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        raw_payload=raw_payload,
        received_at=datetime.now(
            timezone.utc
        )
    )

    db.session.add(
        message
    )

    db.session.commit()

    return jsonify({
        "status": "received",
        "matched": True,
        "maintenance_request_id": (
            candidate.maintenance_request_id
        ),
        "candidate_id": candidate.id
    }), 200

