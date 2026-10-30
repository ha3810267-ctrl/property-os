
import os
import stripe

from flask import Blueprint, request

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from backend.database import db

from backend.models.maintenance_request import (
    MaintenanceRequest
)

from backend.models.user import User


stripe_webhooks_bp = Blueprint(
    "stripe_webhooks",
    __name__
)


# ============================================================
# STRIPE WEBHOOK
# ============================================================

@stripe_webhooks_bp.route(
    "/webhooks/stripe",
    methods=["POST"]
)
def stripe_webhook():

    webhook_secret = os.getenv(
        "STRIPE_WEBHOOK_SECRET"
    )

    if not webhook_secret:
        print(
            "[Stripe webhook] Missing STRIPE_WEBHOOK_SECRET",
            flush=True
        )

        return {
            "error": "Webhook is not configured"
        }, 503

    payload = request.get_data()

    signature = request.headers.get(
        "Stripe-Signature"
    )

    if not signature:
        return {
            "error": "Missing Stripe signature"
        }, 400

    # --------------------------------------------------------
    # Verify Stripe signature
    # --------------------------------------------------------

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            webhook_secret
        )

    except ValueError:
        print(
            "[Stripe webhook] Invalid payload",
            flush=True
        )

        return {
            "error": "Invalid webhook payload"
        }, 400

    except stripe.SignatureVerificationError:
        print(
            "[Stripe webhook] Invalid signature",
            flush=True
        )

        return {
            "error": "Invalid webhook signature"
        }, 400

    event_type = event["type"]

    print(
        f"[Stripe webhook] Received event: {event_type}",
        flush=True
    )

    # --------------------------------------------------------
    # Only process successful Checkout events
    # --------------------------------------------------------

    supported_events = {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded"
    }

    if event_type not in supported_events:
        return {
            "received": True,
            "message": "Event ignored"
        }, 200

    session = event["data"]["object"]
    session = session.to_dict()

    # --------------------------------------------------------
    # Confirm successful payment
    # --------------------------------------------------------

    if session.get("payment_status") != "paid":
        print(
            "[Stripe webhook] Checkout session is not paid",
            flush=True
        )

        return {
            "received": True,
            "message": "Payment not completed"
        }, 200

    if session.get("mode") != "payment":
        return {
            "received": True,
            "message": "Unsupported Checkout mode"
        }, 200

    # --------------------------------------------------------
    # Validate payment details
    # --------------------------------------------------------

    if (
        session.get("amount_total") != 2500
        or session.get("currency") != "gbp"
    ):
        print(
            "[Stripe webhook] Incorrect payment amount or currency",
            flush=True
        )

        return {
            "error": "Payment details do not match"
        }, 400

    session_id = session.get("id")

    metadata = session.get("metadata") or {}

    request_id = metadata.get(
        "maintenance_request_id"
    )

    metadata_user_id = metadata.get(
        "user_id"
    )

    metadata_organisation_id = metadata.get(
        "organisation_id"
    )

    if not session_id or not request_id:
        print(
            "[Stripe webhook] Missing session or request ID",
            flush=True
        )

        return {
            "error": "Missing payment reference"
        }, 400

    try:
        request_id = int(request_id)
    except (TypeError, ValueError):
        return {
            "error": "Invalid maintenance request ID"
        }, 400

    # --------------------------------------------------------
    # Retrieve the Matchly request
    # --------------------------------------------------------

    maintenance_request = db.session.execute(
        select(MaintenanceRequest)
        .where(
            MaintenanceRequest.id == request_id
        )
    ).scalar_one_or_none()

    if not maintenance_request:
        print(
            "[Stripe webhook] Request not found:",
            request_id,
            flush=True
        )

        return {
            "error": "Maintenance request not found"
        }, 404

    # --------------------------------------------------------
    # Verify Checkout session belongs to this request
    # --------------------------------------------------------

    if (
        maintenance_request.stripe_checkout_session_id
        != session_id
    ):
        print(
            "[Stripe webhook] Checkout session mismatch:",
            session_id,
            flush=True
        )

        return {
            "error": "Checkout session does not match request"
        }, 400

    if session.get("client_reference_id") != str(request_id):
        return {
            "error": "Client reference does not match request"
        }, 400

    # --------------------------------------------------------
    # Verify user and organisation metadata
    # --------------------------------------------------------

    if (
        not metadata_user_id
        or str(maintenance_request.user_id)
        != str(metadata_user_id)
    ):
        return {
            "error": "Payment user does not match request"
        }, 400

    user = db.session.execute(
        select(User)
        .where(
            User.id == maintenance_request.user_id
        )
    ).scalar_one_or_none()

    if not user:
        return {
            "error": "Request owner not found"
        }, 404

    if (
        str(user.organisation_id)
        != str(metadata_organisation_id)
    ):
        return {
            "error": "Payment organisation does not match request"
        }, 400

    # --------------------------------------------------------
    # Idempotency: do not process an already-paid request
    # --------------------------------------------------------

    if maintenance_request.payment_status == "paid":
        print(
            "[Stripe webhook] Request already paid:",
            request_id,
            flush=True
        )

        return {
            "received": True,
            "message": "Request already paid"
        }, 200

    # --------------------------------------------------------
    # Mark request as paid
    # --------------------------------------------------------

    payment_intent = session.get(
        "payment_intent"
    )

    if isinstance(payment_intent, dict):
        payment_intent = payment_intent.get("id")

    try:
        maintenance_request.payment_status = "paid"

        maintenance_request.stripe_payment_intent_id = (
            payment_intent
        )

        db.session.commit()

    except SQLAlchemyError as exc:
        db.session.rollback()

        print(
            "[Stripe webhook] Database update failed:",
            repr(exc),
            flush=True
        )

        return {
            "error": "Could not update payment status"
        }, 500

    print(
        "[Stripe webhook] Payment confirmed:",
        f"request={request_id}",
        f"session={session_id}",
        flush=True
    )

    return {
        "received": True,
        "message": "Payment confirmed",
        "maintenance_request_id": request_id,
        "payment_status": "paid"
    }, 200
