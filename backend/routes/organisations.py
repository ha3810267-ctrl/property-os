
from backend.database import db
from backend.models.organisation import Organisation
from sqlalchemy import select
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

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
    ]

@organisations_bp.route("/organisations", methods=["POST"])
def create_organisation():
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    name = data.get("name")

    if not name:
        return {"error": "Organisation name is required"}, 400

    organisation = Organisation(
        name=name
    )

    db.session.add(organisation)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Organisation already exists"}, 409

    return {
        "id": organisation.id,
        "name": organisation.name
    }, 201