from backend.database import db
from backend.models.organisation import Organisation
from backend.models.user import User
from backend.utils.password import validate_password

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from flask import Blueprint, request

from werkzeug.security import generate_password_hash


organisations_bp = Blueprint("organisations", __name__)


@organisations_bp.route("/organisations", methods=["GET"])
def get_organisations():

    organisations = db.session.execute(
        select(Organisation)
    ).scalars().all()

    return [
        {
            "id": organisation.id,
            "name": organisation.name
        }
        for organisation in organisations
    ], 200


@organisations_bp.route("/organisations/signup", methods=["POST"])
def signup_organisation():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body is required"
        }, 400

    organisation_name = data.get("organisation_name")
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not isinstance(organisation_name, str) or not organisation_name.strip():
        return {
            "error": "Organisation name is required"
        }, 400

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

    organisation_name = organisation_name.strip()
    name = name.strip()
    email = email.strip().lower()

    existing_email = db.session.execute(
        select(User).where(
            User.email == email
        )
    ).scalar_one_or_none()

    if existing_email:
        return {
            "error": "Email already exists"
        }, 409

    existing_organisation = db.session.execute(
        select(Organisation).where(
            Organisation.name == organisation_name
        )
    ).scalar_one_or_none()

    if existing_organisation:
        return {
            "error": "Organisation already exists"
        }, 409

    organisation = Organisation(
        name=organisation_name
    )

    db.session.add(organisation)
    db.session.flush()

    admin = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role="admin",
        organisation_id=organisation.id,
        is_active=True
    )

    db.session.add(admin)

    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Could not create organisation"
        }, 409

    return {
        "message": "Organisation created successfully",
        "organisation": {
            "id": organisation.id,
            "name": organisation.name
        },
        "user": {
            "id": admin.id,
            "name": admin.name,
            "email": admin.email,
            "role": admin.role,
            "organisation_id": admin.organisation_id
        }
    }, 201