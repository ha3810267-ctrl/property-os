from sqlalchemy import select, delete
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from backend.database import db
from backend.models.property import Property
from backend.models.tenant import Tenant
from backend.models.maintenance_request import MaintenanceRequest
from backend.models.task_assignment import TaskAssignment

from flask_jwt_extended import jwt_required
from backend.auth import get_current_user


property_bp = Blueprint("property", __name__)


@property_bp.route("/properties", methods=["POST"])
@jwt_required()
def create_property():
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    property_name = data.get("name")
    address = data.get("address")

    if not property_name:
        return {"error": "Property name is required"}, 400

    if not address:
        return {"error": "Property address is required"}, 400

    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    property = Property(
        name=property_name,
        address=address,
        organisation_id=user.organisation_id
    )

    db.session.add(property)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Could not create property"}, 409

    return {
        "id": property.id,
        "name": property.name,
        "address": property.address,
        "organisation_id": property.organisation_id
    }, 201


@property_bp.route("/properties", methods=["GET"])
@jwt_required()
def get_properties():
    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    properties = db.session.execute(
        select(Property).where(
            Property.organisation_id == user.organisation_id
        )
    ).scalars().all()

    return [
        {
            "id": property.id,
            "name": property.name,
            "address": property.address,
            "organisation_id": property.organisation_id
        }
        for property in properties
    ], 200


@property_bp.route("/properties/<int:property_id>", methods=["GET"])
@jwt_required()
def get_property(property_id):
    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    property = db.session.execute(
        select(Property).where(
            Property.id == property_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not property:
        return {"error": "Property not found"}, 404

    return {
        "id": property.id,
        "name": property.name,
        "address": property.address,
        "organisation_id": property.organisation_id
    }, 200


@property_bp.route("/properties/<int:property_id>", methods=["PUT"])
@jwt_required()
def update_property(property_id):
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    new_name = data.get("name")
    new_address = data.get("address")

    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    property = db.session.execute(
        select(Property).where(
            Property.id == property_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not property:
        return {"error": "Property not found"}, 404

    if new_name is not None:
        property.name = new_name

    if new_address is not None:
        property.address = new_address

    if new_name is None and new_address is None:
        return {"error": "At least one field is required"}, 400

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Could not update property"}, 409

    return {
        "id": property.id,
        "name": property.name,
        "address": property.address,
        "organisation_id": property.organisation_id
    }, 200


@property_bp.route(
    "/properties/<int:property_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_property(property_id):
    user = get_current_user()

    if not user:
        return {
            "error": "User not found"
        }, 404

    property = db.session.execute(
        select(Property).where(
            Property.id == property_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not property:
        return {
            "error": "Property not found"
        }, 404

    try:
        tenant_ids = db.session.execute(
            select(Tenant.id).where(
                Tenant.property_id == property.id
            )
        ).scalars().all()

        if tenant_ids:
            maintenance_request_ids = db.session.execute(
                select(MaintenanceRequest.id).where(
                    MaintenanceRequest.tenant_id.in_(tenant_ids)
                )
            ).scalars().all()

            if maintenance_request_ids:
                db.session.execute(
                    delete(TaskAssignment).where(
                        TaskAssignment.maintenance_request_id.in_(
                            maintenance_request_ids
                        )
                    )
                )

                db.session.execute(
                    delete(MaintenanceRequest).where(
                        MaintenanceRequest.id.in_(
                            maintenance_request_ids
                        )
                    )
                )

            db.session.execute(
                delete(Tenant).where(
                    Tenant.id.in_(tenant_ids)
                )
            )

        db.session.delete(property)

        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Could not delete property"
        }, 409

    return {
        "message": "Property deleted successfully",
        "id": property_id
    }, 200