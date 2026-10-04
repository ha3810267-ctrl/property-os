from flask import Blueprint
from flask_jwt_extended import jwt_required
from sqlalchemy import func, select

from backend.database import db
from backend.auth import get_current_user
from backend.models.property import Property
from backend.models.maintenance_request import MaintenanceRequest


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard/stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    user = get_current_user()

    if not user:
        return {"error": "User not found"}, 404

    organisation_id = user.organisation_id

    property_count = db.session.scalar(
        select(func.count(Property.id)).where(
            Property.organisation_id == organisation_id
        )
    ) or 0

    open_maintenance_count = db.session.scalar(
        select(func.count(MaintenanceRequest.id))
        .join(
            Property,
            MaintenanceRequest.property_id == Property.id
        )
        .where(
            Property.organisation_id == organisation_id,
            MaintenanceRequest.status == "open"
        )
    ) or 0

    urgent_issue_count = db.session.scalar(
        select(func.count(MaintenanceRequest.id))
        .join(
            Property,
            MaintenanceRequest.property_id == Property.id
        )
        .where(
            Property.organisation_id == organisation_id,
            MaintenanceRequest.priority == "urgent"
        )
    ) or 0

    return {
        "properties": property_count,
        "open_maintenance": open_maintenance_count,
        "urgent_issues": urgent_issue_count,
    }, 200