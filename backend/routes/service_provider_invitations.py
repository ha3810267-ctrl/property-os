import hashlib
import secrets
from datetime import datetime, timedelta, timezone
import os
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from backend.database import db
from backend.auth import get_current_user
from backend.models.service_provider import ServiceProvider
from backend.models.service_provider_invitation import ServiceProviderInvitation
from backend.models.user import User
from backend.services.email import send_email


service_provider_invitations_bp = Blueprint(
    "service_provider_invitations",
    __name__
)


INVITATION_EXPIRY_DAYS = 7
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)


def hash_invitation_token(token):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def get_manager():

    current_user = get_current_user()

    if not current_user:
        return None, (
            {
                "error": "User not found"
            },
            404
        )

    if current_user.role not in {
        "admin",
        "property_manager"
    }:
        return None, (
            {
                "error": "You do not have permission to manage service providers"
            },
            403
        )

    return current_user, None


def build_invitation_email(
    current_user,
    service_provider,
    raw_token
):

    invitation_url = (
        f"{FRONTEND_URL}/accept-invitation"
        f"?token={raw_token}"
    )

    provider_name = (
        service_provider.name
        or "there"
    )

    business_name = (
        service_provider.business_name
        or "your business"
    )

    html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>You're invited to join Property SaaS</h2>

        <p>Hi {provider_name},</p>

        <p>
            {current_user.name} has invited
            {business_name} to connect with their
            organisation on Property SaaS.
        </p>

        <p>
            Click the button below to accept the invitation
            and create your worker account.
        </p>

        <p>
            <a
                href="{invitation_url}"
                style="
                    display:inline-block;
                    padding:12px 20px;
                    background:#111827;
                    color:white;
                    text-decoration:none;
                    border-radius:6px;
                "
            >
                Accept invitation
            </a>
        </p>

        <p>
            This invitation expires in
            {INVITATION_EXPIRY_DAYS} days.
        </p>

        <p>
            If you were not expecting this invitation,
            you can ignore this email.
        </p>
    </div>
    """

    return html


@service_provider_invitations_bp.route(
    "/service-provider-invitations",
    methods=["GET"]
)
@jwt_required()
def get_service_provider_invitations():

    current_user, error_response = get_manager()

    if error_response:
        return error_response

    now = datetime.now(timezone.utc)

    invitations = db.session.execute(
        select(ServiceProviderInvitation)
        .where(
            ServiceProviderInvitation.organisation_id
            == current_user.organisation_id
        )
        .order_by(
            ServiceProviderInvitation.created_at.desc()
        )
    ).scalars().all()

    response = []

    expired_changed = False

    for invitation in invitations:

        if (
            invitation.status == "pending"
            and invitation.expires_at <= now
        ):
            invitation.status = "expired"
            expired_changed = True

        service_provider = db.session.execute(
            select(ServiceProvider).where(
                ServiceProvider.id
                == invitation.service_provider_id
            )
        ).scalar_one_or_none()

        if not service_provider:
            continue

        response.append({
            "id": invitation.id,
            "service_provider_id": service_provider.id,
            "maintenance_request_id": (
                invitation.maintenance_request_id
            ),
            "status": invitation.status,
            "expires_at": invitation.expires_at.isoformat(),
            "created_at": invitation.created_at.isoformat(),
            "accepted_at": (
                invitation.accepted_at.isoformat()
                if invitation.accepted_at
                else None
            ),
            "provider": {
                "id": service_provider.id,
                "name": service_provider.name,
                "business_name": service_provider.business_name,
                "email": service_provider.email,
                "phone": service_provider.phone,
                "speciality": service_provider.speciality,
                "service_area": service_provider.service_area,
                "is_active": service_provider.is_active,
                "user_id": service_provider.user_id
            }
        })

    if expired_changed:
        db.session.commit()

    return response, 200


@service_provider_invitations_bp.route(
    "/service-provider-invitations",
    methods=["POST"]
)
@jwt_required()
def create_service_provider_invitation():

    current_user, error_response = get_manager()

    if error_response:
        return error_response

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body is required"
        }, 400

    service_provider_id = data.get(
        "service_provider_id"
    )

    maintenance_request_id = data.get(
        "maintenance_request_id"
    )

    if (
        not isinstance(service_provider_id, int)
        or isinstance(service_provider_id, bool)
    ):
        return {
            "error": "Service provider ID must be a valid integer"
        }, 400

    if maintenance_request_id is not None:
        if (
            not isinstance(maintenance_request_id, int)
            or isinstance(maintenance_request_id, bool)
        ):
            return {
                "error": "Maintenance request ID must be a valid integer"
            }, 400

    service_provider = db.session.execute(
        select(ServiceProvider).where(
            ServiceProvider.id == service_provider_id
        )
    ).scalar_one_or_none()

    if not service_provider:
        return {
            "error": "Service provider not found"
        }, 404

    if not service_provider.is_active:
        return {
            "error": "Service provider is inactive"
        }, 400

    if service_provider.user_id:

        linked_user = db.session.execute(
            select(User).where(
                User.id == service_provider.user_id
            )
        ).scalar_one_or_none()

        if linked_user and linked_user.is_active:
            return {
                "error": "Service provider already has an active account"
            }, 409

        if linked_user and not linked_user.is_active:
            service_provider.user_id = None

    existing_invitation = db.session.execute(
        select(ServiceProviderInvitation)
        .where(
            ServiceProviderInvitation.service_provider_id
            == service_provider.id,
            ServiceProviderInvitation.organisation_id
            == current_user.organisation_id,
            ServiceProviderInvitation.status
            == "pending"
        )
    ).scalar_one_or_none()

    if existing_invitation:

        if existing_invitation.expires_at > datetime.now(
            timezone.utc
        ):
            return {
                "error": "This service provider already has a pending invitation",
                "invitation_id": existing_invitation.id
            }, 409

        existing_invitation.status = "expired"

    raw_token = secrets.token_urlsafe(48)

    token_hash = hash_invitation_token(
        raw_token
    )

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=INVITATION_EXPIRY_DAYS)
    )

    invitation = ServiceProviderInvitation(
        service_provider_id=service_provider.id,
        organisation_id=current_user.organisation_id,
        maintenance_request_id=maintenance_request_id,
        token_hash=token_hash,
        expires_at=expires_at,
        status="pending"
    )

    db.session.add(invitation)

    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Invitation could not be created"
        }, 409

    html = build_invitation_email(
        current_user,
        service_provider,
        raw_token
    )

    try:
        send_email(
            to=service_provider.email,
            subject="You're invited to join Property SaaS",
            html=html
        )

    except Exception as error:
        print(
            "Invitation email failed:",
            error
        )

        return {
            "error": (
                "Invitation was created but the email "
                "could not be sent"
            ),
            "invitation_id": invitation.id
        }, 502

    return {
        "id": invitation.id,
        "service_provider_id": invitation.service_provider_id,
        "maintenance_request_id": (
            invitation.maintenance_request_id
        ),
        "status": invitation.status,
        "expires_at": invitation.expires_at.isoformat(),
        "email_sent": True
    }, 201


@service_provider_invitations_bp.route(
    "/service-provider-invitations/<int:invitation_id>/resend",
    methods=["POST"]
)
@jwt_required()
def resend_service_provider_invitation(
    invitation_id
):

    current_user, error_response = get_manager()

    if error_response:
        return error_response

    invitation = db.session.execute(
        select(ServiceProviderInvitation).where(
            ServiceProviderInvitation.id
            == invitation_id,
            ServiceProviderInvitation.organisation_id
            == current_user.organisation_id
        )
    ).scalar_one_or_none()

    if not invitation:
        return {
            "error": "Invitation not found"
        }, 404

    if invitation.status == "accepted":
        return {
            "error": "This invitation has already been accepted"
        }, 409

    service_provider = db.session.execute(
        select(ServiceProvider).where(
            ServiceProvider.id
            == invitation.service_provider_id
        )
    ).scalar_one_or_none()

    if not service_provider:
        return {
            "error": "Service provider not found"
        }, 404

    if not service_provider.is_active:
        return {
            "error": "Service provider is inactive"
        }, 400

    if service_provider.user_id:

        linked_user = db.session.execute(
            select(User).where(
                User.id == service_provider.user_id
            )
        ).scalar_one_or_none()

        if linked_user and linked_user.is_active:
            return {
                "error": "Service provider already has an active account"
            }, 409

        if linked_user and not linked_user.is_active:
            service_provider.user_id = None

    raw_token = secrets.token_urlsafe(48)

    invitation.token_hash = hash_invitation_token(
        raw_token
    )

    invitation.expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=INVITATION_EXPIRY_DAYS)
    )

    invitation.status = "pending"
    invitation.accepted_at = None

    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Invitation could not be resent"
        }, 409

    html = build_invitation_email(
        current_user,
        service_provider,
        raw_token
    )

    try:
        send_email(
            to=service_provider.email,
            subject="You're invited to join Property SaaS",
            html=html
        )

    except Exception as error:
        print(
            "Resent invitation email failed:",
            error
        )

        return {
            "error": (
                "The invitation was updated but "
                "the email could not be sent"
            ),
            "invitation_id": invitation.id
        }, 502

    return {
        "id": invitation.id,
        "service_provider_id": invitation.service_provider_id,
        "status": invitation.status,
        "expires_at": invitation.expires_at.isoformat(),
        "email_sent": True
    }, 200


@service_provider_invitations_bp.route(
    "/service-provider-invitations/accept",
    methods=["POST"]
)
def accept_service_provider_invitation():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body is required"
        }, 400

    token = data.get("token")
    name = data.get("name")
    password = data.get("password")

    if not isinstance(token, str) or not token.strip():
        return {
            "error": "Invitation token is required"
        }, 400

    if not isinstance(name, str) or not name.strip():
        return {
            "error": "Name is required"
        }, 400

    if not isinstance(password, str) or not password:
        return {
            "error": "Password is required"
        }, 400

    token_hash = hash_invitation_token(
        token.strip()
    )

    invitation = db.session.execute(
        select(ServiceProviderInvitation).where(
            ServiceProviderInvitation.token_hash
            == token_hash
        )
    ).scalar_one_or_none()

    if not invitation:
        return {
            "error": "Invalid invitation"
        }, 404

    now = datetime.now(timezone.utc)

    if invitation.status != "pending":
        return {
            "error": "Invitation is no longer active"
        }, 400

    if invitation.expires_at <= now:
        invitation.status = "expired"

        db.session.commit()

        return {
            "error": "Invitation has expired"
        }, 400

    service_provider = db.session.execute(
        select(ServiceProvider).where(
            ServiceProvider.id
            == invitation.service_provider_id
        )
    ).scalar_one_or_none()

    if not service_provider:
        return {
            "error": "Service provider not found"
        }, 404

    if service_provider.user_id:

        linked_user = db.session.execute(
            select(User).where(
                User.id == service_provider.user_id
            )
        ).scalar_one_or_none()

        if linked_user and linked_user.is_active:
            return {
                "error": "Service provider already has an active account"
            }, 409

        if linked_user and not linked_user.is_active:

            linked_user.name = name.strip()

            linked_user.password_hash = (
                generate_password_hash(password)
            )

            linked_user.speciality = (
                service_provider.speciality
            )

            linked_user.is_active = True

            invitation.status = "accepted"
            invitation.accepted_at = now

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()

                return {
                    "error": "Worker account could not be reactivated"
                }, 409

            return {
                "message": "Invitation accepted successfully",
                "user": {
                    "id": linked_user.id,
                    "name": linked_user.name,
                    "email": linked_user.email,
                    "role": linked_user.role,
                    "organisation_id": linked_user.organisation_id
                }
            }, 201

    existing_user = db.session.execute(
        select(User).where(
            User.email
            == service_provider.email.lower()
        )
    ).scalar_one_or_none()

    if existing_user:

        if existing_user.is_active:
            return {
                "error": "An active account already exists with this email"
            }, 409

        if existing_user.role != "worker":
            return {
                "error": "An inactive account already exists with this email"
            }, 409

        existing_user.name = name.strip()

        existing_user.password_hash = (
            generate_password_hash(password)
        )

        existing_user.speciality = (
            service_provider.speciality
        )

        existing_user.is_active = True

        existing_user.organisation_id = (
            invitation.organisation_id
        )

        service_provider.user_id = existing_user.id

        invitation.status = "accepted"
        invitation.accepted_at = now

        try:
            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            return {
                "error": "Worker account could not be reactivated"
            }, 409

        return {
            "message": "Invitation accepted successfully",
            "user": {
                "id": existing_user.id,
                "name": existing_user.name,
                "email": existing_user.email,
                "role": existing_user.role,
                "organisation_id": existing_user.organisation_id
            }
        }, 201

    user = User(
        name=name.strip(),
        email=service_provider.email.lower(),
        password_hash=generate_password_hash(password),
        role="worker",
        speciality=service_provider.speciality,
        is_active=True,
        organisation_id=invitation.organisation_id
    )

    db.session.add(user)

    try:
        db.session.flush()

        service_provider.user_id = user.id

        invitation.status = "accepted"
        invitation.accepted_at = now

        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Worker account could not be created"
        }, 409

    return {
        "message": "Invitation accepted successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "organisation_id": user.organisation_id
        }
    }, 201