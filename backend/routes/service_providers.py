from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import select

from backend.database import db
from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)
from backend.models.maintenance_request import (
    MaintenanceRequest
)
from backend.models.tenant import Tenant
from backend.models.property import Property
from backend.models.service_provider import (
    ServiceProvider
)


service_providers_bp = Blueprint(
    "service_providers",
    __name__
)


def _get_current_user():

    claims = get_jwt()

    return {
        "user_id": claims.get("user_id"),
        "organisation_id": claims.get("organisation_id"),
        "role": claims.get("role")
    }


def _candidate_to_dict(candidate):

    return {
        "id": candidate.id,
        "maintenance_request_id": (
            candidate.maintenance_request_id
        ),
        "provider": candidate.provider,
        "external_id": candidate.external_id,
        "name": candidate.name,
        "trade": candidate.trade,
        "location": candidate.location,
        "website": candidate.website,
        "phone": candidate.phone,
        "email": candidate.email,
        "source_url": candidate.source_url,
        "rating": candidate.rating,
        "review_count": candidate.review_count,
        "availability": candidate.availability,
        "match_score": candidate.match_score,
        "match_reason": candidate.match_reason,
        "contact_status": candidate.contact_status,
        "email_sent_at": (
            candidate.email_sent_at.isoformat()
            if candidate.email_sent_at
            else None
        ),
        "response_received_at": (
            candidate.response_received_at.isoformat()
            if candidate.response_received_at
            else None
        ),
        "last_message": candidate.last_message,
        "gemini_summary": candidate.gemini_summary,
        "response_quality": getattr(
            candidate,
            "response_quality",
            None
        ),
        "quoted_price": candidate.quoted_price,
        "estimated_start": candidate.estimated_start,
        "is_selected": candidate.is_selected,
        "selected_at": (
            candidate.selected_at.isoformat()
            if candidate.selected_at
            else None
        ),
        "created_at": (
            candidate.created_at.isoformat()
            if candidate.created_at
            else None
        ),
        "updated_at": (
            candidate.updated_at.isoformat()
            if candidate.updated_at
            else None
        )
    }


def _get_maintenance_request_for_org(
    maintenance_request_id,
    organisation_id
):

    return db.session.execute(
        select(MaintenanceRequest)
        .join(
            Tenant,
            MaintenanceRequest.tenant_id
            == Tenant.id
        )
        .join(
            Property,
            Tenant.property_id
            == Property.id
        )
        .where(
            MaintenanceRequest.id
            == maintenance_request_id,
            Property.organisation_id
            == organisation_id
        )
    ).scalar_one_or_none()


# ============================================================
# SERVICE PROVIDERS
# ============================================================

@service_providers_bp.route(
    "/service-providers",
    methods=["GET"]
)
@jwt_required()
def get_service_providers():

    current_user = _get_current_user()

    organisation_id = current_user["organisation_id"]

    if not organisation_id:
        return jsonify({
            "error": "User organisation could not be determined"
        }), 400

    providers = (
        ServiceProvider.query
        .filter_by(
            organisation_id=organisation_id,
            is_active=True
        )
        .order_by(
            ServiceProvider.name.asc()
        )
        .all()
    )

    return jsonify([
        {
            "id": provider.id,
            "organisation_id": provider.organisation_id,
            "name": provider.name,
            "business_name": provider.business_name,
            "email": provider.email,
            "phone": provider.phone,
            "speciality": provider.speciality,
            "service_area": provider.service_area,
            "user_id": provider.user_id,
            "is_active": provider.is_active
        }
        for provider in providers
    ]), 200


@service_providers_bp.route(
    "/service-providers",
    methods=["POST"]
)
@jwt_required()
def create_service_provider():

    current_user = _get_current_user()

    organisation_id = current_user["organisation_id"]
    role = current_user["role"]

    if not organisation_id:
        return jsonify({
            "error": "User organisation could not be determined"
        }), 400

    if role not in {
        "admin",
        "property_manager"
    }:
        return jsonify({
            "error": (
                "Only admins and property managers "
                "can create service providers"
            )
        }), 403

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body is required"
        }), 400

    name = data.get("name")
    business_name = data.get("business_name")
    email = data.get("email")
    phone = data.get("phone")
    speciality = data.get("speciality")
    service_area = data.get("service_area")

    if not isinstance(name, str) or not name.strip():
        return jsonify({
            "error": "Service provider name is required"
        }), 400

    if not isinstance(email, str) or not email.strip():
        return jsonify({
            "error": "Service provider email is required"
        }), 400

    provider = ServiceProvider(
        organisation_id=organisation_id,
        name=name.strip(),
        business_name=(
            business_name.strip()
            if isinstance(business_name, str)
            and business_name.strip()
            else None
        ),
        email=email.strip().lower(),
        phone=(
            phone.strip()
            if isinstance(phone, str)
            and phone.strip()
            else None
        ),
        speciality=(
            speciality.strip()
            if isinstance(speciality, str)
            and speciality.strip()
            else None
        ),
        service_area=(
            service_area.strip()
            if isinstance(service_area, str)
            and service_area.strip()
            else None
        ),
        is_active=True
    )

    db.session.add(provider)

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()

        return jsonify({
            "error": "Service provider could not be created"
        }), 409

    return jsonify({
        "id": provider.id,
        "organisation_id": provider.organisation_id,
        "name": provider.name,
        "business_name": provider.business_name,
        "email": provider.email,
        "phone": provider.phone,
        "speciality": provider.speciality,
        "service_area": provider.service_area,
        "user_id": provider.user_id,
        "is_active": provider.is_active
    }), 201


# ============================================================
# EXTERNAL WORKERS
# ============================================================

@service_providers_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>/external-workers",
    methods=["GET"]
)
@jwt_required()
def get_external_workers(
    maintenance_request_id
):

    current_user = _get_current_user()

    organisation_id = (
        current_user["organisation_id"]
    )

    if not organisation_id:
        return jsonify({
            "error": (
                "User organisation could not be determined"
            )
        }), 400

    maintenance_request = (
        _get_maintenance_request_for_org(
            maintenance_request_id,
            organisation_id
        )
    )

    if not maintenance_request:
        return jsonify({
            "error": "Maintenance request not found"
        }), 404

    candidates = (
        ExternalWorkerCandidate.query
        .filter_by(
            maintenance_request_id=
            maintenance_request_id
        )
        .order_by(
            ExternalWorkerCandidate.match_score.desc()
        )
        .all()
    )

    return jsonify({
        "maintenance_request_id":
            maintenance_request_id,
        "external_workers": [
            _candidate_to_dict(candidate)
            for candidate in candidates
        ]
    }), 200


@service_providers_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>/external-workers/<int:candidate_id>",
    methods=["GET"]
)
@jwt_required()
def get_external_worker(
    maintenance_request_id,
    candidate_id
):

    current_user = _get_current_user()

    organisation_id = (
        current_user["organisation_id"]
    )

    maintenance_request = (
        _get_maintenance_request_for_org(
            maintenance_request_id,
            organisation_id
        )
    )

    if not maintenance_request:
        return jsonify({
            "error": "Maintenance request not found"
        }), 404

    candidate = (
        ExternalWorkerCandidate.query
        .filter_by(
            id=candidate_id,
            maintenance_request_id=
                maintenance_request_id
        )
        .first()
    )

    if not candidate:
        return jsonify({
            "error": (
                "External worker candidate not found"
            )
        }), 404

    return jsonify(
        _candidate_to_dict(candidate)
    ), 200


@service_providers_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>/external-workers/<int:candidate_id>/select",
    methods=["POST"]
)
@jwt_required()
def select_external_worker(
    maintenance_request_id,
    candidate_id
):

    current_user = _get_current_user()

    organisation_id = (
        current_user["organisation_id"]
    )

    role = current_user["role"]

    if role not in {
        "admin",
        "property_manager"
    }:
        return jsonify({
            "error": (
                "Only admins and property managers "
                "can select external contractors"
            )
        }), 403

    maintenance_request = (
        _get_maintenance_request_for_org(
            maintenance_request_id,
            organisation_id
        )
    )

    if not maintenance_request:
        return jsonify({
            "error": "Maintenance request not found"
        }), 404

    candidate = (
        ExternalWorkerCandidate.query
        .filter_by(
            id=candidate_id,
            maintenance_request_id=
                maintenance_request_id
        )
        .first()
    )

    if not candidate:
        return jsonify({
            "error": (
                "External worker candidate not found"
            )
        }), 404

    existing_selected = (
        ExternalWorkerCandidate.query
        .filter_by(
            maintenance_request_id=
                maintenance_request_id,
            is_selected=True
        )
        .all()
    )

    for selected_candidate in existing_selected:

        if selected_candidate.id != candidate.id:

            selected_candidate.is_selected = False
            selected_candidate.selected_at = None

    candidate.is_selected = True

    candidate.selected_at = datetime.now(
        timezone.utc
    )

    candidate.updated_at = datetime.now(
        timezone.utc
    )

    db.session.commit()

    return jsonify({
        "message": (
            "External contractor selected"
        ),
        "candidate": _candidate_to_dict(
            candidate
        )
    }), 200