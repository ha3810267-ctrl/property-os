from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.database import db
from backend.auth import get_current_user
from backend.models.maintenance_request import MaintenanceRequest
from backend.models.task_assignment import TaskAssignment
from backend.models.tenant import Tenant
from backend.models.property import Property
from backend.models.user import User


task_assignment_bp = Blueprint("task_assignment", __name__)


@task_assignment_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>/assign",
    methods=["POST"]
)
@jwt_required()
def assign_task(maintenance_request_id):
    data = request.get_json()

    if not data:
        return {"error": "Request body is required"}, 400

    user_id = data.get("user_id")

    if user_id is None:
        return {"error": "User ID is required"}, 400

    if not isinstance(user_id, int) or isinstance(user_id, bool):
        return {"error": "User ID must be a valid integer"}, 400

    current_user = get_current_user()

    if not current_user:
        return {"error": "User not found"}, 404

    if current_user.role not in ["admin", "property_manager"]:
        return {
            "error": "You do not have permission to assign tasks"
        }, 403

    maintenance_request = db.session.execute(
        select(MaintenanceRequest)
        .join(Tenant, MaintenanceRequest.tenant_id == Tenant.id)
        .join(Property, Tenant.property_id == Property.id)
        .where(
            MaintenanceRequest.id == maintenance_request_id,
            Property.organisation_id == current_user.organisation_id
        )
    ).scalar_one_or_none()

    if not maintenance_request:
        return {
            "error": "Maintenance request not found"
        }, 404

    worker = db.session.execute(
        select(User).where(
            User.id == user_id,
            User.organisation_id == current_user.organisation_id,
            User.role == "worker"
        )
    ).scalar_one_or_none()

    if not worker:
        return {
            "error": "Eligible worker not found"
        }, 404

    existing_assignment = db.session.execute(
        select(TaskAssignment).where(
            TaskAssignment.maintenance_request_id == maintenance_request_id
        )
    ).scalar_one_or_none()

    if existing_assignment:
        return {
            "error": "Maintenance request is already assigned"
        }, 409

    assignment = TaskAssignment(
        maintenance_request_id=maintenance_request_id,
        user_id=worker.id,
        assignment_method="manual",
        score=None
    )

    db.session.add(assignment)

    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        return {
            "error": "Task assignment could not be created because the provided information is invalid"
        }, 409

    except SQLAlchemyError:
        db.session.rollback()
        return {
            "error": "Task assignment could not be created"
        }, 500

    return {
        "id": assignment.id,
        "maintenance_request_id": assignment.maintenance_request_id,
        "user_id": assignment.user_id,
        "assigned_at": assignment.assigned_at.isoformat(),
        "assignment_method": assignment.assignment_method,
        "score": assignment.score
    }, 201