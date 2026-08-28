from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from backend.database import db
from backend.models.user import User
from backend.models.organisation import Organisation
from backend.utils.password import validate_password
from backend.auth import get_current_user

from werkzeug.security import generate_password_hash

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["POST"])
@jwt_required()
def create_user():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body is required"
        }, 400

    current_user = get_current_user()

    if not current_user:
        return {
            "error": "User not found"
        }, 404

    if current_user.role not in {
        "admin",
        "property_manager"
    }:
        return {
            "error": "You do not have permission to create users"
        }, 403

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    speciality = data.get("speciality")

    if not isinstance(name, str) or not name.strip():
        return {
            "error": "Name is required"
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

    if role not in {
        "admin",
        "property_manager",
        "worker",
        "landlord",
        "tenant"
    }:
        return {
            "error": "Invalid role"
        }, 400

    if speciality is not None:

        if not isinstance(speciality, str):
            return {
                "error": "Speciality must be a string"
            }, 400

        speciality = speciality.strip()

        if len(speciality) > 500:
            return {
                "error": "Speciality must be 500 characters or fewer"
            }, 400

    email = email.strip().lower()

    organisation = db.session.execute(
        select(Organisation).where(
            Organisation.id == current_user.organisation_id
        )
    ).scalar_one_or_none()

    if not organisation:
        return {
            "error": "Organisation not found"
        }, 404

    user = User(
        name=name.strip(),
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
        speciality=speciality,
        organisation_id=current_user.organisation_id,
        is_active=True
    )

    db.session.add(user)

    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Email already exists"
        }, 409

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "speciality": user.speciality,
        "is_active": user.is_active,
        "organisation_id": user.organisation_id
    }, 201


@users_bp.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    current_user = get_current_user()

    if not current_user:
        return {
            "error": "User not found"
        }, 404

    users = db.session.execute(
        select(User)
        .where(
            User.organisation_id
            == current_user.organisation_id
        )
        .order_by(User.name.asc())
    ).scalars().all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "speciality": user.speciality,
            "is_active": user.is_active,
            "organisation_id": user.organisation_id
        }
        for user in users
    ], 200


@users_bp.route("/workers", methods=["GET"])
@jwt_required()
def get_workers():
    current_user = get_current_user()

    if not current_user:
        return {
            "error": "User not found"
        }, 404

    workers = db.session.execute(
        select(User)
        .where(
            User.organisation_id == current_user.organisation_id,
            User.role == "worker"
        )
        .order_by(User.name.asc())
    ).scalars().all()

    return [
        {
            "id": worker.id,
            "name": worker.name,
            "email": worker.email,
            "role": worker.role,
            "speciality": worker.speciality,
            "is_active": worker.is_active,
            "organisation_id": worker.organisation_id
        }
        for worker in workers
    ], 200


@users_bp.route(
    "/users/<int:user_id>",
    methods=["PUT"]
)
@jwt_required()
def update_user(user_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body is required"
        }, 400

    current_user = get_current_user()

    if not current_user:
        return {
            "error": "User not found"
        }, 404

    if current_user.role not in {
        "admin",
        "property_manager"
    }:
        return {
            "error": "You do not have permission to update users"
        }, 403

    user = db.session.execute(
        select(User).where(
            User.id == user_id,
            User.organisation_id == current_user.organisation_id
        )
    ).scalar_one_or_none()

    if not user:
        return {
            "error": "User not found"
        }, 404

    if user.role != "worker":
        return {
            "error": "Only workers can be updated from this endpoint"
        }, 400

    allowed_fields = {
        "name",
        "email",
        "password",
        "speciality"
    }

    unexpected_fields = set(data.keys()) - allowed_fields

    if unexpected_fields:
        return {
            "error": "Request contains unsupported fields"
        }, 400

    if not data:
        return {
            "error": "At least one field is required"
        }, 400

    if "name" in data:
        name = data.get("name")

        if not isinstance(name, str) or not name.strip():
            return {
                "error": "Name is required"
            }, 400

        user.name = name.strip()

    if "email" in data:
        email = data.get("email")

        if not isinstance(email, str) or not email.strip():
            return {
                "error": "Email is required"
            }, 400

        user.email = email.strip().lower()

    if "password" in data:
        password = data.get("password")

        if not isinstance(password, str) or not password:
            return {
                "error": "Password must be a valid string"
            }, 400

        password_error = validate_password(password)

        if password_error:
            return {
                "error": password_error
            }, 400

        user.password_hash = generate_password_hash(password)

    if "speciality" in data:
        speciality = data.get("speciality")

        if speciality is not None and not isinstance(
            speciality,
            str
        ):
            return {
                "error": "Speciality must be a string"
            }, 400

        speciality = (
            speciality.strip()
            if speciality is not None
            else None
        )

        if speciality and len(speciality) > 500:
            return {
                "error": "Speciality must be 500 characters or fewer"
            }, 400

        user.speciality = speciality

    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Email already exists"
        }, 409

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "speciality": user.speciality,
        "is_active": user.is_active,
        "organisation_id": user.organisation_id
    }, 200


@users_bp.route(
    "/users/<int:user_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_user(user_id):
    current_user = get_current_user()

    if not current_user:
        return {
            "error": "User not found"
        }, 404

    if current_user.role not in {
        "admin",
        "property_manager"
    }:
        return {
            "error": "You do not have permission to deactivate users"
        }, 403

    user = db.session.execute(
        select(User).where(
            User.id == user_id,
            User.organisation_id
            == current_user.organisation_id
        )
    ).scalar_one_or_none()

    if not user:
        return {
            "error": "User not found"
        }, 404

    if user.role != "worker":
        return {
            "error": "Only workers can be deactivated from this endpoint"
        }, 400

    if not user.is_active:
        return {
            "error": "Worker is already inactive"
        }, 400

    user.is_active = False

    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Worker could not be deactivated"
        }, 409

    return {
        "message": "Worker deactivated successfully"
    }, 200
@users_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user_profile():
    current_user = get_current_user()

    if not current_user:
        return {
            "error": "User not found"
        }, 404

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "speciality": current_user.speciality,
        "is_active": current_user.is_active,
        "organisation_id": current_user.organisation_id
    }, 200