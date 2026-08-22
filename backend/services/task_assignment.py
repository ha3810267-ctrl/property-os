from sqlalchemy import select

from backend.database import db
from backend.models.task_assignment import TaskAssignment
from backend.models.user import User
from backend.models.maintenance_request import MaintenanceRequest
from backend.models.tenant import Tenant
from backend.models.property import Property


def calculate_worker_score(worker, maintenance_request):
    speciality = (worker.speciality or "").strip().lower()
    category = (maintenance_request.category or "").strip().lower()
    description = (maintenance_request.description or "").strip().lower()

    if not speciality:
        return 0.0

    if category and category in speciality:
        return 1.0

    speciality_words = set(speciality.replace(",", " ").split())

    if speciality_words:
        description_words = set(
            description.replace(",", " ").split()
        )

        matches = speciality_words.intersection(description_words)

        if matches:
            return min(
                0.9,
                0.5 + (len(matches) * 0.1)
            )

    return 0.1


def assign_task_with_ai(maintenance_request_id):
    maintenance_request = db.session.execute(
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
            MaintenanceRequest.id == maintenance_request_id
        )
    ).scalar_one_or_none()

    if not maintenance_request:
        return None

    organisation_id = db.session.execute(
        select(Property.organisation_id)
        .join(
            Tenant,
            Tenant.property_id == Property.id
        )
        .where(
            Tenant.id == maintenance_request.tenant_id
        )
    ).scalar_one()

    existing_assignment = db.session.execute(
        select(TaskAssignment).where(
            TaskAssignment.maintenance_request_id
            == maintenance_request_id
        )
    ).scalar_one_or_none()

    if existing_assignment:
        return existing_assignment

    workers = db.session.execute(
        select(User).where(
            User.organisation_id == organisation_id,
            User.role == "worker"
        )
    ).scalars().all()

    if not workers:
        return None

    scored_workers = [
        (
            worker,
            calculate_worker_score(
                worker,
                maintenance_request
            )
        )
        for worker in workers
    ]

    best_worker, best_score = max(
        scored_workers,
        key=lambda item: item[1]
    )

    assignment = TaskAssignment(
        maintenance_request_id=maintenance_request.id,
        user_id=best_worker.id,
        assignment_method="ai",
        score=best_score
    )

    db.session.add(assignment)

    return assignment