from sqlalchemy import select
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError
from backend.database import db
from backend.models.tenant import Tenant
from backend.models.property import Property
from flask_jwt_extended import jwt_required
from backend.auth import get_current_user


tenant_bp = Blueprint("tenant", __name__)


@tenant_bp.route("/tenants", methods=["POST"])
@jwt_required()
def create_tenant():
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    name = data.get("name")
    email = data.get("email")
    property_id = data.get("property_id")

    if not name:
        return {"error": "Tenant name is required"}, 400

    if not email:
        return {"error": "Tenant email is required"}, 400

    if not property_id:
        return {"error": "Property ID is required"}, 400

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

    tenant = Tenant(
        name=name,
        email=email,
        property_id=property_id
    )

    db.session.add(tenant)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Could not create tenant"}, 409

    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "property_id": tenant.property_id
    }, 201


@tenant_bp.route("/tenants", methods=["GET"])
@jwt_required()
def get_tenants():
    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    tenants = db.session.execute(
        select(Tenant)
        .join(Property, Tenant.property_id == Property.id)
        .where(
            Property.organisation_id == user.organisation_id
        )
    ).scalars().all()

    return [
        {
            "id": tenant.id,
            "name": tenant.name,
            "email": tenant.email,
            "property_id": tenant.property_id
        }
        for tenant in tenants
    ], 200


@tenant_bp.route("/tenants/<int:tenant_id>", methods=["GET"])
@jwt_required()
def get_tenant(tenant_id):
    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    tenant = db.session.execute(
        select(Tenant)
        .join(Property, Tenant.property_id == Property.id)
        .where(
            Tenant.id == tenant_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not tenant:
        return {"error": "Tenant not found"}, 404

    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "property_id": tenant.property_id
    }, 200


@tenant_bp.route("/tenants/<int:tenant_id>", methods=["PUT"])
@jwt_required()
def update_tenant(tenant_id):
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    name = data.get("name")
    email = data.get("email")
    property_id = data.get("property_id")

    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    tenant = db.session.execute(
        select(Tenant)
        .join(Property, Tenant.property_id == Property.id)
        .where(
            Tenant.id == tenant_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not tenant:
        return {"error": "Tenant not found"}, 404

    if name is not None:
        tenant.name = name

    if email is not None:
        tenant.email = email

    if property_id is not None:
        new_property = db.session.execute(
            select(Property).where(
                Property.id == property_id,
                Property.organisation_id == user.organisation_id
            )
        ).scalar_one_or_none()

        if not new_property:
            return {"error": "Property not found"}, 404

        tenant.property_id = property_id

    if name is None and email is None and property_id is None:
        return {"error": "At least one field is required"}, 400

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Could not update tenant"}, 409

    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "property_id": tenant.property_id
    }, 200


@tenant_bp.route("/tenants/<int:tenant_id>", methods=["DELETE"])
@jwt_required()
def delete_tenant(tenant_id):
    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    tenant = db.session.execute(
        select(Tenant)
        .join(Property, Tenant.property_id == Property.id)
        .where(
            Tenant.id == tenant_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not tenant:
        return {"error": "Tenant not found"}, 404

    db.session.delete(tenant)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Could not delete tenant"}, 409

    return {
        "message": "Tenant deleted successfully",
        "id": tenant_id
    }, 200