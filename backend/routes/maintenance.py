from datetime import datetime, timezone
from html import escape

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


from backend.services.ai_maintenance import (
    analyse_maintenance_request
)

from backend.services.task_assignment import (
    assign_task_with_ai
)

from backend.services.external_worker_search import (
    find_contractors_with_gemini
)

from backend.services.external_worker_ranking import (
    rank_external_workers
)

from backend.services.email import (
    send_email
)


from backend.utils.audit import create_audit_log
from backend.database import db
from backend.auth import get_current_user

from backend.models.maintenance_request import (
    MaintenanceRequest
)

from backend.models.task_assignment import (
    TaskAssignment
)

from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)

from backend.models.external_worker_message import (
    ExternalWorkerMessage
)

from backend.models.tenant import Tenant
from backend.models.property import Property
from backend.models.user import User


maintenance_bp = Blueprint(
    "maintenance",
    __name__
)


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

TARGET_EXTERNAL_CONTRACTORS = 20


# ============================================================
# HELPERS
# ============================================================

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


def maintenance_request_response(
    maintenance_request
):
    assignments = db.session.execute(
        select(
            TaskAssignment,
            User.name
        )
        .join(
            User,
            TaskAssignment.user_id == User.id
        )
        .where(
            TaskAssignment.maintenance_request_id
            == maintenance_request.id
        )
        .order_by(
            TaskAssignment.id
        )
    ).all()

    external_candidates = db.session.execute(
        select(ExternalWorkerCandidate)
        .where(
            ExternalWorkerCandidate.maintenance_request_id
            == maintenance_request.id
        )
        .order_by(
            ExternalWorkerCandidate.match_score.desc().nullslast(),
            ExternalWorkerCandidate.rating.desc().nullslast(),
            ExternalWorkerCandidate.id
        )
        .limit(
            TARGET_EXTERNAL_CONTRACTORS
        )
    ).scalars().all()

    messages = db.session.execute(
        select(ExternalWorkerMessage)
        .where(
            ExternalWorkerMessage.maintenance_request_id
            == maintenance_request.id
        )
        .order_by(
            ExternalWorkerMessage.created_at.desc(),
            ExternalWorkerMessage.id.desc()
        )
    ).scalars().all()

    replies_by_candidate = {}

    for message in messages:

        if message.direction != "inbound":
            continue

        replies_by_candidate.setdefault(
            message.candidate_id,
            []
        ).append({
            "id": message.id,
            "direction": message.direction,
            "resend_message_id": message.resend_message_id,
            "in_reply_to": message.in_reply_to,
            "message_id": message.message_id,
            "sender_email": message.sender_email,
            "recipient_email": message.recipient_email,
            "subject": message.subject,
            "text_body": message.text_body,
            "html_body": message.html_body,
            "received_at": (
                message.received_at.isoformat()
                if message.received_at
                else None
            ),
            "created_at": (
                message.created_at.isoformat()
                if message.created_at
                else None
            )
        })

    return {
        "id": maintenance_request.id,

        "description": maintenance_request.description,

        "tenant_id": maintenance_request.tenant_id,

        "assignments": [
            {
                "id": assignment.id,
                "user_id": assignment.user_id,
                "worker_name": worker_name,
                "assignment_method": (
                    assignment.assignment_method
                ),
                "score": assignment.score
            }
            for assignment, worker_name in assignments
        ],

        "external_workers": [
            {
                "id": candidate.id,
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
                ),

                "replies": replies_by_candidate.get(
                    candidate.id,
                    []
                )
            }
            for candidate in external_candidates
        ],

        "status": maintenance_request.status,

        "priority": maintenance_request.priority,

        "category": maintenance_request.category,

        "created_at": (
            maintenance_request.created_at.isoformat()
        )
    }


def get_property_location_for_request(
    maintenance_request,
    organisation_id
):
    tenant = db.session.execute(
        select(Tenant).where(
            Tenant.id == maintenance_request.tenant_id
        )
    ).scalar_one_or_none()

    if not tenant:
        return None

    property_record = db.session.execute(
        select(Property).where(
            Property.id == tenant.property_id,
            Property.organisation_id == organisation_id
        )
    ).scalar_one_or_none()

    if not property_record:
        return None

    location = getattr(
        property_record,
        "address",
        None
    )

    if not isinstance(location, str):
        return None

    location = location.strip()

    return location or None


def build_external_worker_email(
    maintenance_request,
    property_location
):
    subject = (
        f"Maintenance request – {property_location}"
    )

    safe_category = escape(
        maintenance_request.category
        or "Not specified"
    )

    safe_priority = escape(
        maintenance_request.priority
        or "Not specified"
    )

    safe_location = escape(
        property_location
        or "Not specified"
    )

    safe_description = escape(
        maintenance_request.description
    )

    html = f"""
    <div>
        <h2>Maintenance Request</h2>

        <p>
            <strong>Request #{maintenance_request.id}</strong>
        </p>

        <p>
            <strong>Category:</strong>
            {safe_category}
        </p>

        <p>
            <strong>Priority:</strong>
            {safe_priority}
        </p>

        <p>
            <strong>Location:</strong>
            {safe_location}
        </p>

        <p>
            <strong>Issue:</strong>
        </p>

        <p>
            {safe_description}
        </p>

        <p>
            Please reply to this email with your
            availability and any relevant information
            about completing this work.
        </p>
    </div>
    """

    text_body = (
        "Maintenance Request\n\n"
        f"Request #{maintenance_request.id}\n\n"
        f"Category: "
        f"{maintenance_request.category or 'Not specified'}\n\n"
        f"Priority: "
        f"{maintenance_request.priority or 'Not specified'}\n\n"
        f"Location: "
        f"{property_location or 'Not specified'}\n\n"
        "Issue:\n"
        f"{maintenance_request.description}\n\n"
        "Please reply to this email with your "
        "availability and any relevant "
        "information about completing the work."
    )

    return subject, html, text_body



def automatically_contact_external_workers(
    maintenance_request,
    candidates,
    organisation_id
):
    """
    Automatically emails every newly discovered contractor
    that has a public email address.

    Contractors without an email are skipped.

    Only candidates passed into this function are contacted.
    """

    print(
        "[contractor email] function called: "
        f"{len(candidates)} candidates",
        flush=True
    )

    property_location = get_property_location_for_request(
        maintenance_request,
        organisation_id
    )

    subject, html, text_body = (
        build_external_worker_email(
            maintenance_request,
            property_location
        )
    )

    sent = []
    skipped = []
    failed = []

    for candidate in candidates:

        email = (
            candidate.email.strip()
            if isinstance(candidate.email, str)
            else None
        )

        if not email:

            print(
                "[contractor email] skipped: "
                f"candidate={candidate.id}, "
                f"name={candidate.name!r}, "
                "reason=no email",
                flush=True
            )

            skipped.append({
                "candidate_id": candidate.id,
                "contractor": candidate.name,
                "reason": "No public email address found"
            })

            continue

        print(
            "[contractor email] calling send_email: "
            f"candidate={candidate.id}, "
            f"name={candidate.name!r}, "
            f"email={email!r}",
            flush=True
        )

        try:

            result = send_email(
                to=email,
                subject=subject,
                html=html
            )

            print(
                "[contractor email] send_email returned: "
                f"{result!r}",
                flush=True
            )

            resend_message_id = None

            if isinstance(result, dict):

                resend_message_id = (
                    result.get("id")
                    or result.get("email_id")
                )

            else:

                resend_message_id = getattr(
                    result,
                    "id",
                    None
                )

            message = ExternalWorkerMessage(
                maintenance_request_id=(
                    maintenance_request.id
                ),
                candidate_id=candidate.id,
                direction="outbound",
                resend_message_id=resend_message_id,
                sender_email=None,
                recipient_email=email,
                subject=subject,
                text_body=text_body,
                html_body=html,
                received_at=None
            )

            db.session.add(
                message
            )

            db.session.commit()

            sent.append({
                "candidate_id": candidate.id,
                "contractor": candidate.name,
                "email": email,
                "resend_message_id": resend_message_id
            })

            print(
                "[contractor email] sent: "
                f"candidate={candidate.id}, "
                f"name={candidate.name!r}, "
                f"email={email!r}, "
                f"resend_id={resend_message_id!r}",
                flush=True
            )

        except Exception as exc:

            db.session.rollback()

            print(
                "[contractor email] failed: "
                f"candidate={candidate.id}, "
                f"name={candidate.name!r}, "
                f"email={email!r}, "
                f"error={exc!r}",
                flush=True
            )

            failed.append({
                "candidate_id": candidate.id,
                "contractor": candidate.name,
                "email": email,
                "error": str(exc)
            })

    print(
        "[contractor email] function finished: "
        f"sent={len(sent)}, "
        f"skipped={len(skipped)}, "
        f"failed={len(failed)}",
        flush=True
    )

    return sent, skipped, failed




# ============================================================
# CREATE MAINTENANCE REQUEST
# ============================================================

@maintenance_bp.route(
    "/maintenance-requests",
    methods=["POST"]
)
@jwt_required()
def create_maintenance_request():

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):
        return {
            "error": (
                "Request body must be a valid JSON object"
            )
        }, 400

    description = data.get("description")
    tenant_id = data.get("tenant_id")

    if (
        not isinstance(description, str)
        or not description.strip()
    ):
        return {
            "error": (
                "Maintenance description is required"
            )
        }, 400

    description = description.strip()

    user = get_current_user()

    if not user:
        return {
            "error": "User not found"
        }, 404

    if user.role == "tenant":

        if not user.tenant_id:
            return {
                "error": (
                    "Tenant account is not properly configured"
                )
            }, 403

        tenant_id = user.tenant_id

    else:

        if (
            not isinstance(tenant_id, int)
            or isinstance(tenant_id, bool)
        ):
            return {
                "error": (
                    "Tenant ID must be a valid integer"
                )
            }, 400

    try:

        ai_result = analyse_maintenance_request(
            description
        )

    except ValueError as exc:

        return {
            "error": str(exc)
        }, 422

    tenant = db.session.execute(
        select(Tenant)
        .join(
            Property,
            Tenant.property_id == Property.id
        )
        .where(
            Tenant.id == tenant_id,
            Property.organisation_id
            == user.organisation_id
        )
    ).scalar_one_or_none()

    if not tenant:
        return {
            "error": "Tenant not found"
        }, 404

    maintenance_request = MaintenanceRequest(
        description=description,
        tenant_id=tenant_id,
        priority=ai_result["priority"],
        category=ai_result["category"]
    )

    db.session.add(
        maintenance_request
    )

    try:

        db.session.flush()

        assignments = assign_task_with_ai(
            maintenance_request.id,
            ai_result["required_trades"]
        )

        create_audit_log(
            user=user,
            action="maintenance_request_created",
            resource_type="maintenance_request",
            resource_id=maintenance_request.id
        )

        if assignments:
            create_audit_log(
                user=user,
                action="maintenance_request_ai_assigned",
                resource_type="maintenance_request",
                resource_id=maintenance_request.id
            )

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return {
            "error": (
                "Maintenance request could not be created "
                "because the provided information is invalid"
            )
        }, 409

    except SQLAlchemyError:

        db.session.rollback()

        return {
            "error": (
                "Maintenance request could not be created"
            )
        }, 500

    return maintenance_request_response(
        maintenance_request
    ), 201


# ============================================================
# GET ALL MAINTENANCE REQUESTS
# ============================================================

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

    query = (
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
            Property.organisation_id
            == user.organisation_id
        )
        .order_by(
            MaintenanceRequest.created_at.desc()
        )
    )

    if user.role == "tenant":

        if not user.tenant_id:
            return {
                "error": (
                    "Tenant account is not properly configured"
                )
            }, 403

        query = query.where(
            MaintenanceRequest.tenant_id
            == user.tenant_id
        )

    maintenance_requests = db.session.execute(
        query
    ).scalars().all()

    return [
        maintenance_request_response(
            maintenance_request
        )
        for maintenance_request
        in maintenance_requests
    ], 200


# ============================================================
# GET SINGLE MAINTENANCE REQUEST
# ============================================================

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

    maintenance_request = (
        get_maintenance_request_for_user(
            maintenance_request_id,
            user.organisation_id
        )
    )

    if not maintenance_request:
        return {
            "error": (
                "Maintenance request not found"
            )
        }, 404

    if user.role == "tenant":

        if (
            not user.tenant_id
            or maintenance_request.tenant_id
            != user.tenant_id
        ):
            return {
                "error": (
                    "Maintenance request not found"
                )
            }, 404

    return maintenance_request_response(
        maintenance_request
    ), 200


# ============================================================
# MANUAL INTERNAL WORKER ASSIGNMENT
# ============================================================

@maintenance_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>/assign",
    methods=["POST"]
)
@jwt_required()
def manually_assign_maintenance_request(
    maintenance_request_id
):

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
            "error": (
                "You do not have permission to assign "
                "maintenance requests"
            )
        }, 403

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):
        return {
            "error": (
                "Request body must be a valid JSON object"
            )
        }, 400

    user_id = data.get("user_id")

    if (
        not isinstance(user_id, int)
        or isinstance(user_id, bool)
    ):
        return {
            "error": (
                "Worker ID must be a valid integer"
            )
        }, 400

    maintenance_request = (
        get_maintenance_request_for_user(
            maintenance_request_id,
            user.organisation_id
        )
    )

    if not maintenance_request:
        return {
            "error": (
                "Maintenance request not found"
            )
        }, 404

    worker = db.session.execute(
        select(User).where(
            User.id == user_id,
            User.organisation_id
            == user.organisation_id,
            User.role == "worker",
            User.is_active.is_(True)
        )
    ).scalar_one_or_none()

    if not worker:
        return {
            "error": "Worker not found"
        }, 404

    existing_assignment = db.session.execute(
        select(TaskAssignment).where(
            TaskAssignment.maintenance_request_id
            == maintenance_request.id,
            TaskAssignment.user_id
            == worker.id
        )
    ).scalar_one_or_none()

    if existing_assignment:
        return maintenance_request_response(
            maintenance_request
        ), 200

    try:

        assignment = TaskAssignment(
            maintenance_request_id=(
                maintenance_request.id
            ),
            user_id=worker.id,
            assignment_method="manual",
            score=None
        )

        db.session.add(
            assignment
        )

        db.session.flush()

        create_audit_log(
            user=user,
            action=(
                "maintenance_request_manual_assignment_added"
            ),
            resource_type="maintenance_request",
            resource_id=maintenance_request.id
        )

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return {
            "error": (
                "Worker is already assigned to "
                "this request"
            )
        }, 409

    except SQLAlchemyError:

        db.session.rollback()

        return {
            "error": (
                "Maintenance request could not be "
                "manually assigned"
            )
        }, 500

    return maintenance_request_response(
        maintenance_request
    ), 200


# ============================================================
# REMOVE INTERNAL WORKER ASSIGNMENT
# ============================================================

@maintenance_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>/assign/<int:worker_id>",
    methods=["DELETE"]
)
@jwt_required()
def remove_maintenance_assignment(
    maintenance_request_id,
    worker_id
):

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
            "error": (
                "You do not have permission to "
                "remove assignments"
            )
        }, 403

    maintenance_request = (
        get_maintenance_request_for_user(
            maintenance_request_id,
            user.organisation_id
        )
    )

    if not maintenance_request:
        return {
            "error": (
                "Maintenance request not found"
            )
        }, 404

    assignment = db.session.execute(
        select(TaskAssignment)
        .join(
            User,
            TaskAssignment.user_id == User.id
        )
        .where(
            TaskAssignment.maintenance_request_id
            == maintenance_request.id,
            TaskAssignment.user_id == worker_id,
            User.organisation_id
            == user.organisation_id
        )
    ).scalar_one_or_none()

    if not assignment:
        return {
            "error": (
                "Worker is not assigned to this request"
            )
        }, 404

    try:

        db.session.delete(
            assignment
        )

        create_audit_log(
            user=user,
            action=(
                "maintenance_request_assignment_removed"
            ),
            resource_type="maintenance_request",
            resource_id=maintenance_request.id
        )

        db.session.commit()

    except SQLAlchemyError:

        db.session.rollback()

        return {
            "error": (
                "Assignment could not be removed"
            )
        }, 500

    return maintenance_request_response(
        maintenance_request
    ), 200


# ============================================================
# GEMINI CONTRACTOR DISCOVERY
# + LOCATION-AWARE RANKING
# + AUTOMATIC EMAIL
# ============================================================

@maintenance_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>/external-workers/search",
    methods=["POST"]
)
@jwt_required()
def search_external_workers_for_request(
    maintenance_request_id
):

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
            "error": (
                "You do not have permission to search "
                "for external contractors"
            )
        }, 403

    maintenance_request = (
        get_maintenance_request_for_user(
            maintenance_request_id,
            user.organisation_id
        )
    )

    if not maintenance_request:
        return {
            "error": (
                "Maintenance request not found"
            )
        }, 404

    data = request.get_json(
        silent=True
    )

    if data is None:
        data = {}

    if not isinstance(data, dict):
        return {
            "error": (
                "Request body must be a valid JSON object"
            )
        }, 400

    location = data.get("location")

    if location is not None:

        if not isinstance(location, str):
            return {
                "error": "Location must be a string"
            }, 400

        location = location.strip()

        if not location:
            location = None

    # --------------------------------------------------------
    # Determine required trades
    # --------------------------------------------------------

    try:

        ai_result = analyse_maintenance_request(
            maintenance_request.description
        )

        required_trades = ai_result.get(
            "required_trades",
            []
        )

    except ValueError as exc:

        return {
            "error": str(exc)
        }, 422

    if not required_trades:
        return {
            "error": (
                "Could not determine the required "
                "external contractor trade"
            )
        }, 422

    # --------------------------------------------------------
    # Determine property location
    # --------------------------------------------------------

    if not location:

        location = get_property_location_for_request(
            maintenance_request,
            user.organisation_id
        )

    # --------------------------------------------------------
    # Existing candidates
    # --------------------------------------------------------

    existing_candidates = db.session.execute(
        select(ExternalWorkerCandidate)
        .where(
            ExternalWorkerCandidate.maintenance_request_id
            == maintenance_request.id
        )
    ).scalars().all()

    existing_keys = {
        (
            candidate.provider,
            candidate.external_id
        )
        for candidate in existing_candidates
    }

    # --------------------------------------------------------
    # Gemini contractor discovery
    # --------------------------------------------------------

    print(
        "[external search] started: "
        f"request={maintenance_request.id}, "
        f"trades={required_trades}, "
        f"location={location!r}, "
        f"existing={len(existing_candidates)}",
        flush=True
    )

    try:

        candidates = find_contractors_with_gemini(
            maintenance_request_id=maintenance_request.id,
            required_trades=required_trades,
            location=location
        )

        print(
            "[external search] Gemini returned "
            f"{len(candidates)} candidate(s)",
            flush=True
        )

        for candidate in candidates:

            print(
                "[external search] candidate: "
                f"name={candidate.name!r}, "
                f"trade={candidate.trade!r}, "
                f"email={candidate.email!r}, "
                f"location={candidate.location!r}, "
                f"source={candidate.source_url!r}",
                flush=True
            )

    except ValueError as exc:

        print(
            "[external search] Gemini validation error: "
            f"{exc!r}",
            flush=True
        )

        return {
            "error": str(exc)
        }, 422

    except Exception as exc:

        print(
            "[external search] Gemini discovery error: "
            f"{exc!r}",
            flush=True
        )

        return {
            "error": (
                "Gemini could not find external contractors"
            )
        }, 500

    if not isinstance(candidates, list):

        return {
            "error": (
                "Gemini contractor search returned "
                "an invalid result"
            )
        }, 500

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    new_candidates = []

    for candidate in candidates:

        if not isinstance(
            candidate,
            ExternalWorkerCandidate
        ):
            continue

        candidate_key = (
            candidate.provider,
            candidate.external_id
        )

        if candidate_key in existing_keys:
            continue

        candidate.maintenance_request_id = (
            maintenance_request.id
        )

        new_candidates.append(
            candidate
        )

        existing_keys.add(
            candidate_key
        )

    print(
        "[external search] "
        f"{len(new_candidates)} new candidate(s) remain "
        "after duplicate filtering",
        flush=True
    )

    # --------------------------------------------------------
    # Combine existing + new candidates
    #
    # Ranking is performed against the full pool so the final
    # displayed/contacted set is the strongest 20 candidates.
    # --------------------------------------------------------

    ranking_pool = (
        list(existing_candidates)
        + list(new_candidates)
    )

    ranking_error = None

    if ranking_pool:

        try:

            ranking_pool = rank_external_workers(
                maintenance_description=(
                    maintenance_request.description
                ),
                required_trades=required_trades,
                candidates=ranking_pool,
                target_location=location
            )

        except Exception as exc:

            ranking_error = str(exc)

            print(
                "[external search] contractor ranking error:",
                repr(exc),
                flush=True
            )

            for candidate in new_candidates:

                candidate.match_score = None
                candidate.match_reason = None

    # --------------------------------------------------------
    # Final top 20
    # --------------------------------------------------------

    final_candidates = ranking_pool[
        :TARGET_EXTERNAL_CONTRACTORS
    ]

    final_candidate_ids = {
        candidate.id
        for candidate in final_candidates
        if candidate.id is not None
    }

    final_new_candidates = [
        candidate
        for candidate in final_candidates
        if candidate in new_candidates
    ]

    # --------------------------------------------------------
    # Save candidates
    # --------------------------------------------------------

    added_candidates = []

    try:

        for candidate in new_candidates:

            if candidate not in final_new_candidates:
                continue

            db.session.add(
                candidate
            )

            added_candidates.append(
                candidate
            )

        db.session.flush()

        create_audit_log(
            user=user,
            action=(
                "maintenance_gemini_contractor_search"
            ),
            resource_type="maintenance_request",
            resource_id=maintenance_request.id
        )

        if ranking_pool:

            create_audit_log(
                user=user,
                action=(
                    "maintenance_gemini_contractor_ranking"
                ),
                resource_type="maintenance_request",
                resource_id=maintenance_request.id
            )

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return {
            "error": (
                "External contractor candidates "
                "could not be created"
            )
        }, 409

    except SQLAlchemyError:

        db.session.rollback()

        return {
            "error": (
                "External contractor candidates "
                "could not be saved"
            )
        }, 500

    # --------------------------------------------------------
    # AUTOMATIC CONTRACTOR EMAIL
    #
    # Only newly discovered contractors that made the final
    # top-20 set are contacted.
    # --------------------------------------------------------

    sent = []
    skipped = []
    email_failed = []

    if added_candidates:

        (
            sent,
            skipped,
            email_failed
        ) = automatically_contact_external_workers(
            maintenance_request=maintenance_request,
            candidates=added_candidates,
            organisation_id=user.organisation_id
        )

        if sent:

            try:

                create_audit_log(
                    user=user,
                    action=(
                        "maintenance_external_worker_emails_sent"
                    ),
                    resource_type="maintenance_request",
                    resource_id=maintenance_request.id
                )

                db.session.commit()

            except SQLAlchemyError:

                db.session.rollback()

                print(
                    "[contractor email] "
                    "emails were sent but email audit "
                    "log could not be saved",
                    flush=True
                )

    # --------------------------------------------------------
    # Return discovery + ranking + email results
    # --------------------------------------------------------

    response = {
        "message": (
            "Gemini discovered and ranked "
            "external contractors"
        ),

        "required_trades": required_trades,

        "location": location,

        "discovered": len(
            added_candidates
        ),

        "total_candidates": len(
            final_candidates
        ),

        "target_candidates": TARGET_EXTERNAL_CONTRACTORS,

        "ranking": (
            "completed"
            if ranking_error is None
            else "failed"
        ),

        "emails": {
            "sent": sent,
            "skipped": skipped,
            "failed": email_failed
        },

        "maintenance_request": (
            maintenance_request_response(
                maintenance_request
            )
        )
    }

    if ranking_error:

        response["ranking_warning"] = (
            "Contractors were discovered successfully "
            "but contractor ranking failed"
        )

    if len(final_candidates) < TARGET_EXTERNAL_CONTRACTORS:

        response["contractor_count_warning"] = (
            "Fewer than 20 qualifying contractors "
            "were available after geographic expansion "
            "and public-email filtering"
        )

    print(
        "[external search] complete: "
        f"discovered={response['discovered']}, "
        f"final_candidates={response['total_candidates']}, "
        f"ranking={response['ranking']}, "
        f"emails_sent={len(sent)}, "
        f"emails_skipped={len(skipped)}, "
        f"emails_failed={len(email_failed)}",
        flush=True
    )

    return response, 200


# ============================================================
# SELECT / DESELECT EXTERNAL CONTRACTOR
# ============================================================

@maintenance_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>/external-workers/<int:candidate_id>/select",
    methods=["POST"]
)
@jwt_required()
def select_external_worker(
    maintenance_request_id,
    candidate_id
):

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
            "error": (
                "You do not have permission to "
                "select an external contractor"
            )
        }, 403

    maintenance_request = (
        get_maintenance_request_for_user(
            maintenance_request_id,
            user.organisation_id
        )
    )

    if not maintenance_request:
        return {
            "error": (
                "Maintenance request not found"
            )
        }, 404

    candidate = db.session.execute(
        select(ExternalWorkerCandidate)
        .where(
            ExternalWorkerCandidate.id
            == candidate_id,
            ExternalWorkerCandidate.maintenance_request_id
            == maintenance_request.id
        )
    ).scalar_one_or_none()

    if not candidate:
        return {
            "error": (
                "External contractor candidate "
                "not found"
            )
        }, 404

    try:

        if candidate.is_selected:

            candidate.is_selected = False
            candidate.selected_at = None

            audit_action = (
                "maintenance_external_worker_deselected"
            )

        else:

            candidate.is_selected = True
            candidate.selected_at = (
                datetime.now(timezone.utc)
            )

            audit_action = (
                "maintenance_external_worker_selected"
            )

        create_audit_log(
            user=user,
            action=audit_action,
            resource_type="maintenance_request",
            resource_id=maintenance_request.id
        )

        db.session.commit()

    except SQLAlchemyError:

        db.session.rollback()

        return {
            "error": (
                "External contractor selection "
                "could not be updated"
            )
        }, 500

    return maintenance_request_response(
        maintenance_request
    ), 200


# ============================================================
# UPDATE MAINTENANCE REQUEST
# ============================================================

@maintenance_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>",
    methods=["PUT"]
)
@jwt_required()
def update_maintenance_request(
    maintenance_request_id
):

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):
        return {
            "error": (
                "Request body must be a valid JSON object"
            )
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
            "error": (
                "You do not have permission to "
                "update this request"
            )
        }, 403

    maintenance_request = (
        get_maintenance_request_for_user(
            maintenance_request_id,
            user.organisation_id
        )
    )

    if not maintenance_request:
        return {
            "error": (
                "Maintenance request not found"
            )
        }, 404

    allowed_fields = {
        "status",
        "priority",
        "category"
    }

    unexpected_fields = (
        set(data.keys())
        - allowed_fields
    )

    if unexpected_fields:
        return {
            "error": (
                "Request contains unsupported fields"
            )
        }, 400

    if not data:
        return {
            "error": (
                "At least one field is required"
            )
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
                "error": (
                    "Invalid maintenance request status"
                )
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
                "error": (
                    "Invalid maintenance request priority"
                )
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
                "error": (
                    "Category cannot be empty"
                )
            }, 400

        if len(category) > 100:
            return {
                "error": (
                    "Category must be 100 characters "
                    "or fewer"
                )
            }, 400

        maintenance_request.category = category

    try:

        if status == "completed":

            db.session.execute(
                delete(TaskAssignment).where(
                    TaskAssignment
                    .maintenance_request_id
                    == maintenance_request.id
                )
            )

            db.session.execute(
                delete(ExternalWorkerMessage).where(
                    ExternalWorkerMessage
                    .maintenance_request_id
                    == maintenance_request.id
                )
            )

            db.session.execute(
                delete(
                    ExternalWorkerCandidate
                ).where(
                    ExternalWorkerCandidate
                    .maintenance_request_id
                    == maintenance_request.id
                )
            )

            create_audit_log(
                user=user,
                action=(
                    "maintenance_request_completed"
                ),
                resource_type="maintenance_request",
                resource_id=maintenance_request.id
            )

            db.session.delete(
                maintenance_request
            )

        else:

            db.session.flush()

            create_audit_log(
                user=user,
                action=(
                    "maintenance_request_updated"
                ),
                resource_type="maintenance_request",
                resource_id=maintenance_request.id
            )

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return {
            "error": (
                "Maintenance request could not be "
                "updated because the provided "
                "information is invalid"
            )
        }, 409

    except SQLAlchemyError:

        db.session.rollback()

        return {
            "error": (
                "Maintenance request could "
                "not be updated"
            )
        }, 500

    if status == "completed":

        return {
            "message": (
                "Maintenance request completed "
                "and removed"
            ),
            "id": maintenance_request_id
        }, 200

    return maintenance_request_response(
        maintenance_request
    ), 200


# ============================================================
# DELETE MAINTENANCE REQUEST
# ============================================================

@maintenance_bp.route(
    "/maintenance-requests/<int:maintenance_request_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_maintenance_request(
    maintenance_request_id
):

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
            "error": (
                "You do not have permission to "
                "delete this request"
            )
        }, 403

    maintenance_request = (
        get_maintenance_request_for_user(
            maintenance_request_id,
            user.organisation_id
        )
    )

    if not maintenance_request:
        return {
            "error": (
                "Maintenance request not found"
            )
        }, 404

    try:

        db.session.execute(
            delete(TaskAssignment).where(
                TaskAssignment
                .maintenance_request_id
                == maintenance_request.id
            )
        )

        db.session.execute(
            delete(ExternalWorkerMessage).where(
                ExternalWorkerMessage
                .maintenance_request_id
                == maintenance_request.id
            )
        )

        db.session.execute(
            delete(
                ExternalWorkerCandidate
            ).where(
                ExternalWorkerCandidate
                .maintenance_request_id
                == maintenance_request.id
            )
        )

        create_audit_log(
            user=user,
            action=(
                "maintenance_request_deleted"
            ),
            resource_type="maintenance_request",
            resource_id=maintenance_request.id
        )

        db.session.delete(
            maintenance_request
        )

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return {
            "error": (
                "Maintenance request could "
                "not be deleted"
            )
        }, 409

    except SQLAlchemyError:

        db.session.rollback()

        return {
            "error": (
                "Maintenance request could "
                "not be deleted"
            )
        }, 500

    return {
        "message": (
            "Maintenance request deleted successfully"
        ),
        "id": maintenance_request_id
    }, 200