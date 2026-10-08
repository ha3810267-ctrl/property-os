import os

from flask import Blueprint, jsonify, request

from backend.services.email import send_email


contact_bp = Blueprint(
    "contact",
    __name__,
    url_prefix="/contact"
)


CONTACT_EMAIL = "adam.hagras@yahoo.com"


@contact_bp.route(
    "",
    methods=["POST"]
)
def submit_contact():

    data = request.get_json(silent=True) or {}

    name = str(
        data.get("name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip()

    subject = str(
        data.get("subject", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    if not name:
        return jsonify({
            "error": "Name is required."
        }), 400

    if not email:
        return jsonify({
            "error": "Email address is required."
        }), 400

    if not subject:
        return jsonify({
            "error": "Subject is required."
        }), 400

    if not message:
        return jsonify({
            "error": "Message is required."
        }), 400

    if len(name) > 120:
        return jsonify({
            "error": "Name is too long."
        }), 400

    if len(email) > 254:
        return jsonify({
            "error": "Email address is too long."
        }), 400

    if len(subject) > 200:
        return jsonify({
            "error": "Subject is too long."
        }), 400

    if len(message) > 5000:
        return jsonify({
            "error": "Message is too long."
        }), 400

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({
            "error": "Please enter a valid email address."
        }), 400

    html = f"""
        <h2>New PropertyOS Contact Message</h2>

        <p>
            <strong>Name:</strong>
            {name}
        </p>

        <p>
            <strong>Email:</strong>
            {email}
        </p>

        <p>
            <strong>Subject:</strong>
            {subject}
        </p>

        <hr>

        <p>
            {message.replace(chr(10), "<br>")}
        </p>
    """

    try:
        send_email(
            to=CONTACT_EMAIL,
            subject=f"PropertyOS Contact: {subject}",
            html=html
        )

    except Exception as exc:
        print(
            "CONTACT EMAIL ERROR:",
            repr(exc)
        )

        return jsonify({
            "error": "Failed to send your message. Please try again."
        }), 500

    return jsonify({
        "message": "Your message has been sent successfully."
    }), 200