from flask import Blueprint, request
from backend.database import db
from backend.models.user import User
from backend.models.organisation import Organisation
from backend.utils.password import validate_password
from werkzeug.security import generate_password_hash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    organisation_id = data.get("organisation_id")

    if not name:
        return {"error": "Name is required"}, 400

    if not email:
        return {"error": "Email is required"}, 400

    if not password:
        return {"error": "Password is required"}, 400

    password_error = validate_password(password)

    if password_error:
        return {"error": password_error}, 400

    if not role:
        return {"error": "Role is required"}, 400

    if not organisation_id:
        return {"error": "Organisation ID is required"}, 400

    organisation = db.session.execute(
        select(Organisation).where(
            Organisation.id == organisation_id
        )
    ).scalar_one_or_none()

    if not organisation:
        return {"error": "Organisation not found"}, 404

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
        organisation_id=organisation_id
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
        "organisation_id": user.organisation_id
    }, 201