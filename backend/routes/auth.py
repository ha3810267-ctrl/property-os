from flask import Blueprint, request
from sqlalchemy import select
from backend.database import db
from backend.models.user import User
from werkzeug.security import check_password_hash


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

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "organisation_id": user.organisation_id
    }, 200