from flask import Blueprint, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from backend.database import db
from backend.models.user import User
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from backend.auth import get_current_user
from backend.utils.password import validate_password


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    email = data.get("email")
    password = data.get("password")

    if not email:
        return {"error": "Email is required"}, 400

    if not password:
        return {"error": "Password is required"}, 400

    user = db.session.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if not user:
        return {"error": "Invalid email or password"}, 401

    if not check_password_hash(user.password_hash, password):
        return {"error": "Invalid email or password"}, 401

    access_token = create_access_token(identity=str(user.id))

    return {
        "access_token": access_token,
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "organisation_id": user.organisation_id
    }, 200


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
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if not user:
        return {
            "message": "If an account exists for this email, a password reset link will be sent"
        }, 200

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    user.password_reset_token_hash = token_hash

    user.password_reset_expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=30)
    )

    db.session.commit()

    # Email delivery will be added later

    return {
        "message": "If an account exists for this email, a password reset link will be sent"
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
        or user.password_reset_expires_at <= datetime.now(timezone.utc)
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

    db.session.commit()

    return {
        "message": "Password changed successfully"
    }, 200