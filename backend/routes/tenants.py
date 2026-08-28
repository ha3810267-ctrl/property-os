from sqlalchemy import select, delete
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from backend.database import db
from backend.models.tenant import Tenant
from backend.models.property import Property
from backend.models.user import User
from backend.models.maintenance_request import MaintenanceRequest
from backend.models.task_assignment import TaskAssignment

from flask_jwt_extended import jwt_required
from backend.auth import get_current_user


tenant_bp = Blueprint("tenant", __name__)


@tenant_bp.route("/tenants", methods=["POST"])
@jwt_required()
def create_tenant():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "Request body is required"}, 400

    name = data.get("name")
    email = data.get("email")
    property_id = data.get("property_id")

    if not isinstance(name, str) or not name.strip():
        return {"error": "Tenant name is required"}, 400

    if not isinstance(email, str) or not email.strip():
        return {"error": "Tenant email is required"}, 400

    if not property_id:
        return {"error": "Property ID is required"}, 400

    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    if user.role not in {"admin", "property_manager"}:
        return {
            "error": "You do not have permission to create tenants"
        }, 403

    property = db.session.execute(
        select(Property).where(
            Property.id == property_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not property:
        return {"error": "Property not found"}, 404

    email = email.strip().lower()

    existing_tenant = db.session.execute(
        select(Tenant).where(
            Tenant.email == email
        )
    ).scalar_one_or_none()

    if existing_tenant:
        return {
            "error": "A tenant with this email already exists"
        }, 409

    tenant = Tenant(
        name=name.strip(),
        email=email,
        property_id=property_id
    )

    db.session.add(tenant)

    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Could not create tenant"
        }, 409

    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "property_id": tenant.property_id,
        "account_created": False
    }, 201


@tenant_bp.route("/tenant/me", methods=["GET"])
@jwt_required()
def get_current_tenant():

    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    if user.role != "tenant" or not user.tenant_id:
        return {"error": "Tenant access required"}, 403

    tenant = db.session.execute(
        select(Tenant)
        .join(
            Property,
            Tenant.property_id == Property.id
        )
        .where(
            Tenant.id == user.tenant_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not tenant:
        return {"error": "Tenant profile not found"}, 404

    property = db.session.execute(
        select(Property).where(
            Property.id == tenant.property_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not property:
        return {"error": "Tenant property not found"}, 404

    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "property_id": tenant.property_id,
        "property": {
            "id": property.id,
            "name": getattr(property, "name", None),
            "address": getattr(property, "address", None)
        }
    }, 200


@tenant_bp.route("/tenants", methods=["GET"])
@jwt_required()
def get_tenants():

    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    tenants = db.session.execute(
        select(Tenant)
        .join(
            Property,
            Tenant.property_id == Property.id
        )
        .where(
            Property.organisation_id == user.organisation_id
        )
    ).scalars().all()

    return [
        {
            "id": tenant.id,
            "name": tenant.name,
            "email": tenant.email,
            "property_id": tenant.property_id,
            "account_created": db.session.execute(
                select(User.id).where(
                    User.tenant_id == tenant.id
                )
            ).scalar_one_or_none() is not None
        }
        for tenant in tenants
    ], 200


@tenant_bp.route(
    "/tenants/<int:tenant_id>",
    methods=["GET"]
)
@jwt_required()
def get_tenant(tenant_id):

    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    tenant = db.session.execute(
        select(Tenant)
        .join(
            Property,
            Tenant.property_id == Property.id
        )
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


@tenant_bp.route(
    "/tenants/<int:tenant_id>",
    methods=["PUT"]
)
@jwt_required()
def update_tenant(tenant_id):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "Request body is required"}, 400

    name = data.get("name")
    email = data.get("email")
    property_id = data.get("property_id")

    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    if user.role not in {"admin", "property_manager"}:
        return {
            "error": "You do not have permission to update tenants"
        }, 403

    tenant = db.session.execute(
        select(Tenant)
        .join(
            Property,
            Tenant.property_id == Property.id
        )
        .where(
            Tenant.id == tenant_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not tenant:
        return {"error": "Tenant not found"}, 404

    if name is not None:
        if not isinstance(name, str) or not name.strip():
            return {"error": "Tenant name is required"}, 400

        tenant.name = name.strip()

    if email is not None:
        if not isinstance(email, str) or not email.strip():
            return {"error": "Tenant email is required"}, 400

        email = email.strip().lower()

        existing_user = db.session.execute(
            select(User).where(
                User.email == email,
                User.id != user.id
            )
        ).scalar_one_or_none()

        if existing_user:
            return {"error": "Email already exists"}, 409

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

    if (
        name is None
        and email is None
        and property_id is None
    ):
        return {"error": "At least one field is required"}, 400

    tenant_user = db.session.execute(
        select(User).where(
            User.tenant_id == tenant.id
        )
    ).scalar_one_or_none()

    if tenant_user:

        if name is not None:
            tenant_user.name = tenant.name

        if email is not None:
            tenant_user.email = tenant.email

        if property_id is not None:
            tenant_user.organisation_id = user.organisation_id

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


@tenant_bp.route(
    "/tenants/<int:tenant_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_tenant(tenant_id):

    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    if user.role not in {"admin", "property_manager"}:
        return {
            "error": "You do not have permission to delete tenants"
        }, 403

    tenant = db.session.execute(
        select(Tenant)
        .join(
            Property,
            Tenant.property_id == Property.id
        )
        .where(
            Tenant.id == tenant_id,
            Property.organisation_id == user.organisation_id
        )
    ).scalar_one_or_none()

    if not tenant:
        return {"error": "Tenant not found"}, 404

    try:

        tenant_user = db.session.execute(
            select(User).where(
                User.tenant_id == tenant.id
            )
        ).scalar_one_or_none()

        if tenant_user:
            tenant_user.is_active = False
            tenant_user.tenant_id = None

        maintenance_request_ids = db.session.execute(
            select(MaintenanceRequest.id).where(
                MaintenanceRequest.tenant_id == tenant.id
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

        db.session.delete(tenant)

        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Could not delete tenant"
        }, 409

    return {
        "message": "Tenant deleted successfully",
        "id": tenant_id
    }, 200