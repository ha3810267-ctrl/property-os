
import re

import resend

from flask import Blueprint, request

from backend.database import db

from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)

from backend.models.maintenance_request import (
    MaintenanceRequest
)

from backend.services.contractor_response_processing import (
    process_contractor_response
)


resend_webhook_bp = Blueprint(
    "resend_webhook",
    __name__
)


# ============================================================
# RESEND CLIENT
# ============================================================

def _get_resend_client():
    import os

    api_key = os.getenv("RESEND_API_KEY")

    if not api_key:
        raise RuntimeError(
            "RESEND_API_KEY is not configured"
        )

    resend.api_key = api_key


# ============================================================
# EMAIL HELPERS
# ============================================================

def _extract_email_address(value):
    if not isinstance(value, str):
        return ""

    match = re.search(
        r"<([^>]+)>",
        value
    )

    if match:
        return match.group(1).strip().lower()

    return value.strip().lower()


def _find_candidate(
    sender_email,
    subject
):
    candidates = ExternalWorkerCandidate.query.filter(
        ExternalWorkerCandidate.email.isnot(None)
    ).all()

    sender_email = sender_email.lower()

    # --------------------------------------------------------
    # Match by contractor email
    # --------------------------------------------------------

    for candidate in candidates:

        candidate_email = (
            candidate.email.strip().lower()
            if candidate.email
            else ""
        )

        if candidate_email == sender_email:
            return candidate

    # --------------------------------------------------------
    # Fallback match by contractor name in subject
    # --------------------------------------------------------

    if isinstance(subject, str):

        subject_lower = subject.lower()

        for candidate in candidates:

            if (
                candidate.name
                and candidate.name.lower()
                in subject_lower
            ):
                return candidate

    return None


def _extract_received_email_body(
    received_email
):
    if isinstance(received_email, dict):

        email_text = received_email.get(
            "text"
        )

        if not email_text:
            email_text = received_email.get(
                "html"
            )

        return email_text

    email_text = getattr(
        received_email,
        "text",
        None
    )

    if not email_text:
        email_text = getattr(
            received_email,
            "html",
            None
        )

    return email_text


# ============================================================
# RESEND WEBHOOK
# ============================================================

@resend_webhook_bp.route(
    "/webhooks/resend",
    methods=["POST"]
)
def resend_webhook():

    payload = request.get_json(
        silent=True
    )

    if not isinstance(payload, dict):
        return {
            "error": "Invalid webhook payload"
        }, 400

    event_type = payload.get(
        "type"
    )

    # --------------------------------------------------------
    # Ignore events that are not incoming email
    # --------------------------------------------------------

    if event_type != "email.received":

        return {
            "received": True,
            "ignored": True
        }, 200

    data = payload.get(
        "data"
    )

    if not isinstance(data, dict):

        return {
            "error": "Invalid email event data"
        }, 400

    email_id = data.get(
        "email_id"
    )

    if not email_id:

        return {
            "error": "Missing email_id"
        }, 400

    sender = data.get(
        "from",
        ""
    )

    subject = data.get(
        "subject",
        ""
    )

    sender_email = _extract_email_address(
        sender
    )

    if not sender_email:

        return {
            "error": "Could not determine sender"
        }, 400

    print(
        "[resend webhook] incoming email:",
        sender_email,
        subject
    )

    # ========================================================
    # RETRIEVE FULL EMAIL FROM RESEND
    # ========================================================

    try:

        _get_resend_client()

        received_email = (
            resend.Emails.Receiving.get(
                email_id
            )
        )

    except Exception as exc:

        print(
            "[resend webhook] email retrieval error:",
            repr(exc)
        )

        return {
            "error": "Could not retrieve received email"
        }, 500

    email_text = _extract_received_email_body(
        received_email
    )

    if not email_text:

        return {
            "received": True,
            "ignored": True,
            "reason": "Email contained no readable body"
        }, 200

    # ========================================================
    # FIND CONTRACTOR
    # ========================================================

    candidate = _find_candidate(
        sender_email,
        subject
    )

    if not candidate:

        print(
            "[resend webhook] no contractor matched:",
            sender_email
        )

        return {
            "received": True,
            "ignored": True,
            "reason": "No matching contractor"
        }, 200

    print(
        "[resend webhook] matched contractor:",
        candidate.id,
        candidate.name
    )

    # ========================================================
    # FIND MAINTENANCE REQUEST
    # ========================================================

    maintenance_request = db.session.get(
        MaintenanceRequest,
        candidate.maintenance_request_id
    )

    if not maintenance_request:

        print(
            "[resend webhook] maintenance request not found:",
            candidate.maintenance_request_id
        )

        return {
            "received": True,
            "ignored": True,
            "reason": "Maintenance request not found"
        }, 200

    # ========================================================
    # PROCESS CONTRACTOR RESPONSE
    # ========================================================

    try:

        result = process_contractor_response(
            candidate=candidate,
            maintenance_request=maintenance_request,
            contractor_response=email_text
        )

    except Exception as exc:

        db.session.rollback()

        print(
            "[resend webhook] contractor response processing error:",
            repr(exc)
        )

        return {
            "error": "Contractor response could not be processed"
        }, 500

    # ========================================================
    # COMPLETE
    # ========================================================

    analysis = result.get(
        "analysis",
        {}
    )

    print(
        "[resend webhook] contractor response processed:",
        candidate.name,
        analysis
    )

    return {
        "received": True,
        "processed": True,
        "candidate_id": candidate.id,
        "analysis": analysis
    }, 200

