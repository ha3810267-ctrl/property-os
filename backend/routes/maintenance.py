from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.utils.audit import create_audit_log
from backend.database import db
from backend.auth import get_current_user
from backend.models.maintenance_request import MaintenanceRequest
from backend.models.tenant import Tenant
from backend.models.property import Property


maintenance_bp = Blueprint("maintenance", __name__)


ALLOWED_STATUSES = {
    "open",
    "in_progress",
    "completed",
    "cancelled"
}

ALLOWED_PRIORITIES = {
    "low",
    "normal",
    "high",
    "urgent"
}


def get_maintenance_request_for_user(
    maintenance_request_id,
    organisation_id
):
    return db.session.execute(
        select(MaintenanceRequest)
        .join(
            Tenant,
            MaintenanceRequest.tenant_id == Tenant.id
        )
        .join(
            Property,
            Tenant.property_id == Property.id
        )
        .where(
            MaintenanceRequest.id == maintenance_request_id,
            Property.organisation_id == organisation_id
        )
    ).scalar_one_or_none()


def maintenance_request_response(maintenance_request):
    return {
        "id": maintenance_request.id,
        "description": maintenance_request.description,
        "tenant_id": maintenance_request.tenant_id,
        "assigned_to": maintenance_request.assigned_to,
        "status": maintenance_request.status,
        "priority": maintenance_request.priority,
        "category": maintenance_request.category,
        "created_at": maintenance_request.created_at.isoformat()
    }


@maintenance_bp.route(
    "/maintenance-requests",
    methods=["POST"]
)
@jwt_required()
def create_maintenance_request():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body must be a valid JSON object"
        }, 400

    description = data.get("description")
    tenant_id = data.get("tenant_id")

    if not isinstance(description, str) or not description.strip():
        return {
            "error": "Maintenance description is required"
        }, 400

    if not isinstance(tenant_id, int) or isinstance(tenant_id, bool):
        return {
            "error": "Tenant ID must be a valid integer"
        }, 400

    description = description.strip()

    user = get_current_user()

    if not user:
        return {
            "error": "User not found"
        }, 404

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
        return {
            "error": "Tenant not found"
        }, 404

    maintenance_request = MaintenanceRequest(
        description=description,
        tenant_id=tenant_id
    )

    db.session.add(maintenance_request)

    try:
        db.session.flush()

        create_audit_log(
            user=user,
            action="maintenance_request_created",
            resource_type="maintenance_request",
            resource_id=maintenance_request.id
        )

        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Maintenance request could not be created because the provided information is invalid"
        }, 409

    except SQLAlchemyError:
        db.session.rollback()

        return {
            "error": "Maintenance request could not be created"
        }, 500

    return maintenance_request_response(
        maintenance_request
    ), 201


@maintenance_bp.route(
    "/maintenance-requests",
    methods=["GET"]
)
@jwt_required()
def get_maintenance_requests():

    user = get_current_user()

    if not user:
        return {
            "error": "User not found"
        }, 404

    maintenance_requests = db.session.execute(
        select(MaintenanceRequest)
        .join(
            Tenant,
            MaintenanceRequest.tenant_id == Tenant.id
        )
        .join(
            Property,
            Tenant.property_id == Property.id
        )
        .where(
            Property.organisation_id == user.organisation_id
        )
        .order_by(
            MaintenanceRequest.created_at.desc()
        )
    ).scalars().all()

    return [
        maintenance_request_response(
            maintenance_request
        )
        for maintenance_request in maintenance_requests
    ], 200


@maintenance_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>",
    methods=["GET"]
)
@jwt_required()
def get_maintenance_request(
    maintenance_request_id
):

    user = get_current_user()

    if not user:
        return {
            "error": "User not found"
        }, 404

    maintenance_request = get_maintenance_request_for_user(
        maintenance_request_id,
        user.organisation_id
    )

    if not maintenance_request:
        return {
            "error": "Maintenance request not found"
        }, 404

    return maintenance_request_response(
        maintenance_request
    ), 200


@maintenance_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>",
    methods=["PUT"]
)
@jwt_required()
def update_maintenance_request(
    maintenance_request_id
):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "error": "Request body must be a valid JSON object"
        }, 400

    user = get_current_user()

    if not user:
        return {
            "error": "User not found"
        }, 404

    if user.role not in {
        "admin",
        "property_manager"
    }:
        return {
            "error": "You do not have permission to update this request"
        }, 403

    maintenance_request = get_maintenance_request_for_user(
        maintenance_request_id,
        user.organisation_id
    )

    if not maintenance_request:
        return {
            "error": "Maintenance request not found"
        }, 404

    allowed_fields = {
        "status",
        "priority",
        "category"
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

    status = data.get("status")
    priority = data.get("priority")
    category = data.get("category")

    if status is not None:

        if not isinstance(status, str):
            return {
                "error": "Status must be a string"
            }, 400

        status = status.strip().lower()

        if status not in ALLOWED_STATUSES:
            return {
                "error": "Invalid maintenance request status"
            }, 400

        maintenance_request.status = status

    if priority is not None:

        if not isinstance(priority, str):
            return {
                "error": "Priority must be a string"
            }, 400

        priority = priority.strip().lower()

        if priority not in ALLOWED_PRIORITIES:
            return {
                "error": "Invalid maintenance request priority"
            }, 400

        maintenance_request.priority = priority

    if category is not None:

        if not isinstance(category, str):
            return {
                "error": "Category must be a string"
            }, 400

        category = category.strip()

        if not category:
            return {
                "error": "Category cannot be empty"
            }, 400

        if len(category) > 100:
            return {
                "error": "Category must be 100 characters or fewer"
            }, 400

        maintenance_request.category = category

    try:
        db.session.flush()

        create_audit_log(
            user=user,
            action="maintenance_request_updated",
            resource_type="maintenance_request",
            resource_id=maintenance_request.id
        )

        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Maintenance request could not be updated because the provided information is invalid"
        }, 409

    except SQLAlchemyError:
        db.session.rollback()

        return {
            "error": "Maintenance request could not be updated"
        }, 500

    return maintenance_request_response(
        maintenance_request
    ), 200