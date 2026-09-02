from flask import Blueprint, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import os
from backend.database import db
from backend.models.user import User
from backend.models.tenant import Tenant
from backend.models.property import Property

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from flask_jwt_extended import (
    create_access_token,
    jwt_required
)

from datetime import datetime, timedelta, timezone

import hashlib
import secrets

from backend.auth import get_current_user
from backend.utils.password import validate_password
from backend.services.email import send_email


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body is required"
        }, 400

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not email.strip():
        return {
            "error": "Email is required"
        }, 400

    if not isinstance(password, str) or not password:
        return {
            "error": "Password is required"
        }, 400

    user = db.session.execute(
        select(User).where(
            User.email == email.strip().lower()
        )
    ).scalar_one_or_none()

    if not user:
        return {
            "error": "Invalid email or password"
        }, 401

    if not user.is_active:
        return {
            "error": "Account is inactive"
        }, 403

    if not check_password_hash(
        user.password_hash,
        password
    ):
        return {
            "error": "Invalid email or password"
        }, 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "tenant_id": user.tenant_id,
            "organisation_id": user.organisation_id
        }
    )

    return {
        "access_token": access_token,
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "organisation_id": user.organisation_id,
        "tenant_id": user.tenant_id
    }, 200


@auth_bp.route("/tenant-signup", methods=["POST"])
def tenant_signup():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body is required"
        }, 400

    tenant_id = data.get("tenant_id")
    email = data.get("email")
    password = data.get("password")

    if not tenant_id:
        return {
            "error": "Tenant ID is required"
        }, 400

    if not isinstance(email, str) or not email.strip():
        return {
            "error": "Email is required"
        }, 400

    if not isinstance(password, str) or not password:
        return {
            "error": "Password is required"
        }, 400

    password_error = validate_password(password)

    if password_error:
        return {
            "error": password_error
        }, 400

    try:
        tenant_id = int(tenant_id)

    except (TypeError, ValueError):
        return {
            "error": "Invalid tenant ID"
        }, 400

    email = email.strip().lower()

    tenant = db.session.execute(
        select(Tenant).where(
            Tenant.id == tenant_id,
            Tenant.email == email
        )
    ).scalar_one_or_none()

    if not tenant:
        return {
            "error": "Tenant account could not be verified"
        }, 404

    existing_user = db.session.execute(
        select(User).where(
            User.tenant_id == tenant.id
        )
    ).scalar_one_or_none()

    if existing_user:
        return {
            "error": "A tenant account already exists"
        }, 409

    existing_email = db.session.execute(
        select(User).where(
            User.email == email
        )
    ).scalar_one_or_none()

    if existing_email:
        return {
            "error": "An account with this email already exists"
        }, 409

    property = db.session.execute(
        select(Property).where(
            Property.id == tenant.property_id
        )
    ).scalar_one_or_none()

    if not property:
        return {
            "error": "Tenant property could not be found"
        }, 404

    tenant_user = User(
        name=tenant.name,
        email=email,
        password_hash=generate_password_hash(password),
        role="tenant",
        speciality=None,
        is_active=True,
        organisation_id=property.organisation_id,
        tenant_id=tenant.id
    )

    db.session.add(tenant_user)

    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Could not create tenant account"
        }, 409

    except SQLAlchemyError:
        db.session.rollback()

        return {
            "error": "Could not create tenant account"
        }, 500

    access_token = create_access_token(
        identity=str(tenant_user.id),
        additional_claims={
            "role": tenant_user.role,
            "tenant_id": tenant_user.tenant_id,
            "organisation_id": tenant_user.organisation_id
        }
    )

    return {
        "message": "Tenant account created successfully",
        "access_token": access_token,
        "id": tenant_user.id,
        "name": tenant_user.name,
        "email": tenant_user.email,
        "role": tenant_user.role,
        "organisation_id": tenant_user.organisation_id,
        "tenant_id": tenant_user.tenant_id
    }, 201

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body must be a valid JSON object"
        }, 400

    email = data.get("email")

    if not isinstance(email, str) or not email.strip():
        return {
            "error": "Email is required"
        }, 400

    email = email.strip().lower()

    user = db.session.execute(
        select(User).where(
            User.email == email
        )
    ).scalar_one_or_none()

    # Do not reveal whether an account exists
    if not user:
        return {
            "message": (
                "If an account exists for this email, "
                "a password reset link will be sent"
            )
        }, 200

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    user.password_reset_token_hash = token_hash

    user.password_reset_expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=30)
    )

    try:
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        return {
            "error": "Password reset could not be started"
        }, 500

    frontend_url = os.getenv("FRONTEND_URL")

    if not frontend_url:
        return {
            "error": "Password reset is not configured correctly"
        }, 500

    frontend_url = frontend_url.rstrip("/")

    reset_url = (
        f"{frontend_url}/reset-password"
        f"?token={raw_token}"
    )

    try:

        send_email(
            to=user.email,
            subject="Reset your PropertyOS password",
            html=f"""
                <div
                    style="
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        max-width: 600px;
                        margin: 0 auto;
                    "
                >

                    <h2>
                        Reset your PropertyOS password
                    </h2>

                    <p>
                        We received a request to reset
                        your PropertyOS password.
                    </p>

                    <p>
                        Click the button below to choose
                        a new password.
                    </p>

                    <p>
                        <a
                            href="{reset_url}"
                            style="
                                display: inline-block;
                                padding: 12px 20px;
                                background: #111827;
                                color: #ffffff;
                                text-decoration: none;
                                border-radius: 6px;
                            "
                        >
                            Reset password
                        </a>
                    </p>

                    <p>
                        This link will expire in 30 minutes.
                    </p>

                    <p>
                        If you did not request a password reset,
                        you can safely ignore this email.
                    </p>

                </div>
            """
        )

    except Exception:
        return {
            "error": "Password reset email could not be sent"
        }, 500

    return {
        "message": (
            "If an account exists for this email, "
            "a password reset link will be sent"
        )
    }, 200

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body must be a valid JSON object"
        }, 400

    token = data.get("token")
    new_password = data.get("new_password")

    if not isinstance(token, str) or not token.strip():
        return {
            "error": "Reset token is required"
        }, 400

    if not isinstance(new_password, str) or not new_password:
        return {
            "error": "New password is required"
        }, 400

    password_error = validate_password(new_password)

    if password_error:
        return {
            "error": password_error
        }, 400

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    user = db.session.execute(
        select(User).where(
            User.password_reset_token_hash == token_hash
        )
    ).scalar_one_or_none()

    if not user:
        return {
            "error": "Invalid or expired reset token"
        }, 400

    if (
        not user.password_reset_expires_at
        or user.password_reset_expires_at
        <= datetime.now(timezone.utc)
    ):

        user.password_reset_token_hash = None
        user.password_reset_expires_at = None

        try:
            db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()

        return {
            "error": "Invalid or expired reset token"
        }, 400

    try:

        user.password_hash = generate_password_hash(
            new_password
        )

        user.password_reset_token_hash = None
        user.password_reset_expires_at = None

        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        return {
            "error": "Password reset could not be completed"
        }, 500

    return {
        "message": "Password reset successfully"
    }, 200


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body must be a valid JSON object"
        }, 400

    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not isinstance(current_password, str) or not current_password:
        return {
            "error": "Current password is required"
        }, 400

    if not isinstance(new_password, str) or not new_password:
        return {
            "error": "New password is required"
        }, 400

    password_error = validate_password(new_password)

    if password_error:
        return {
            "error": password_error
        }, 400

    if current_password == new_password:
        return {
            "error": "New password must be different from current password"
        }, 400

    user = get_current_user()

    if not user:
        return {
            "error": "User not found"
        }, 404

    if not check_password_hash(
        user.password_hash,
        current_password
    ):
        return {
            "error": "Current password is incorrect"
        }, 401

    user.password_hash = generate_password_hash(
        new_password
    )

    try:

        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()

        return {
            "error": "Password change could not be completed"
        }, 500

    return {
        "message": "Password changed successfully"
    }, 200