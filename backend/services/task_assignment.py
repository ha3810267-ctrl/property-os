import json
import os
import traceback

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from backend.database import db
from backend.models.task_assignment import TaskAssignment
from backend.models.user import User
from backend.models.maintenance_request import MaintenanceRequest
from backend.models.tenant import Tenant
from backend.models.property import Property
from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)
from backend.services.external_worker_search import (
    search_external_workers
)


def _get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured"
        )

    return OpenAI(
        api_key=api_key
    )


def _safe_score(value):
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None

    if score < 0:
        return 0.0

    if score > 1:
        return 1.0

    return score


def _safe_string(value):
    if value is None:
        return ""

    if not isinstance(value, str):
        value = str(value)

    return value.strip()


def _extract_trade_names(required_trades):
    trade_names = []

    for trade_info in required_trades or []:

        if isinstance(trade_info, dict):
            trade = trade_info.get(
                "trade",
                ""
            )
        else:
            trade = str(trade_info)

        trade = _safe_string(
            trade
        ).lower()

        if trade and trade not in trade_names:
            trade_names.append(
                trade
            )

    return trade_names


def _rank_internal_workers(
    maintenance_request,
    required_trades,
    workers
):
    """
    Use OpenAI to rank eligible internal workers.

    OpenAI recommends workers based on the maintenance
    request and worker specialities.

    The backend remains responsible for validating that
    returned worker IDs are eligible.
    """

    if not workers:
        return []

    trade_names = _extract_trade_names(
        required_trades
    )

    worker_data = []

    for worker in workers:

        worker_data.append(
            {
                "id": worker.id,
                "name": worker.name,
                "speciality": worker.speciality
            }
        )

    prompt = f"""
You are the internal worker assignment intelligence
system for a property management platform.

Choose the most suitable internal worker for the
maintenance request.

Maintenance request:

Description:
{maintenance_request.description}

Category:
{maintenance_request.category or "Unknown"}

Priority:
{maintenance_request.priority or "Unknown"}

Issue:
{getattr(maintenance_request, "issue", None) or "Unknown"}

Required trades:
{json.dumps(trade_names)}

Eligible internal workers:
{json.dumps(worker_data)}

Return ONLY valid JSON using exactly this structure:

{{
    "ranked_workers": [
        {{
            "id": 123,
            "score": 0.94,
            "reason": "Strong speciality match for the required trade."
        }}
    ]
}}

Rules:

1. Return every eligible worker exactly once.

2. Use the worker ID supplied in the worker data.

3. Score must be a number between 0 and 1.

4. Higher scores mean stronger suitability.

5. Consider:
   - speciality match
   - required trade match
   - relevance to the maintenance issue
   - category relevance
   - priority where relevant to suitability

6. Only use information provided in the
   maintenance request and worker data.

7. Do not invent worker skills or experience.

8. Do not assume skills that are not supported by
   the worker speciality.

9. A worker with no relevant speciality should
   receive a low score.

10. Keep the reason concise and factual.

11. Sort workers from highest score to lowest score.

12. Return every worker exactly once.

13. Do not select external contractors.

14. Return ONLY valid JSON.
"""

    client = _get_openai_client()

    try:
        response = client.chat.completions.create(
            model=os.getenv(
                "OPENAI_MODEL",
                "gpt-4o"
            ),
            response_format={
                "type": "json_object"
            },
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a reliable internal "
                        "worker assignment system."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

    except Exception as exc:
        raise RuntimeError(
            f"OpenAI internal worker ranking failed: {exc}"
        ) from exc

    output = response.choices[0].message.content

    if not output:
        raise RuntimeError(
            "OpenAI returned an empty worker ranking"
        )

    try:
        data = json.loads(
            output
        )

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "OpenAI returned invalid worker ranking JSON"
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            "OpenAI returned an invalid worker ranking structure"
        )

    ranked_workers = data.get(
        "ranked_workers"
    )

    if not isinstance(
        ranked_workers,
        list
    ):
        raise RuntimeError(
            "OpenAI returned an invalid ranked_workers structure"
        )

    worker_by_id = {
        worker.id: worker
        for worker in workers
    }

    results = []
    seen_ids = set()

    for ranked_worker in ranked_workers:

        if not isinstance(
            ranked_worker,
            dict
        ):
            continue

        worker_id = ranked_worker.get(
            "id"
        )

        try:
            worker_id = int(
                worker_id
            )
        except (
            TypeError,
            ValueError
        ):
            continue

        if worker_id in seen_ids:
            continue

        worker = worker_by_id.get(
            worker_id
        )

        if not worker:
            continue

        score = _safe_score(
            ranked_worker.get(
                "score"
            )
        )

        if score is None:
            continue

        reason = _safe_string(
            ranked_worker.get(
                "reason"
            )
        )

        results.append(
            {
                "worker": worker,
                "score": score,
                "reason": reason
            }
        )

        seen_ids.add(
            worker_id
        )

    return results


def get_property_location(
    maintenance_request
):
    result = db.session.execute(
        select(Property)
        .join(
            Tenant,
            Tenant.property_id == Property.id
        )
        .where(
            Tenant.id
            == maintenance_request.tenant_id
        )
    ).scalar_one_or_none()

    if not result:
        return None

    return getattr(
        result,
        "location",
        None
    )


def save_external_candidates(
    maintenance_request_id,
    candidates
):
    saved_candidates = []

    for candidate in candidates:

        existing = db.session.execute(
            select(ExternalWorkerCandidate)
            .where(
                ExternalWorkerCandidate.maintenance_request_id
                == maintenance_request_id,
                ExternalWorkerCandidate.provider
                == candidate.provider,
                ExternalWorkerCandidate.external_id
                == candidate.external_id
            )
        ).scalar_one_or_none()

        if existing:
            saved_candidates.append(
                existing
            )
            continue

        db.session.add(
            candidate
        )

        saved_candidates.append(
            candidate
        )

    return saved_candidates


def assign_task_with_ai(
    maintenance_request_id,
    required_trades=None
):
    """
    Assign suitable internal workers using OpenAI.

    If one or more required trades cannot be covered
    by suitable internal workers, external contractor
    discovery is attempted through Gemini.

    External discovery is optional and must never prevent
    the maintenance request from continuing.

    Gemini errors are printed with a full traceback for
    debugging but are swallowed so the request can continue.
    """

    maintenance_request = db.session.execute(
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
            == maintenance_request_id
        )
    ).scalar_one_or_none()

    if not maintenance_request:
        return []

    organisation_id = db.session.execute(
        select(Property.organisation_id)
        .join(
            Tenant,
            Tenant.property_id == Property.id
        )
        .where(
            Tenant.id
            == maintenance_request.tenant_id
        )
    ).scalar_one_or_none()

    if organisation_id is None:
        return []

    existing_assignments = db.session.execute(
        select(TaskAssignment)
        .where(
            TaskAssignment.maintenance_request_id
            == maintenance_request_id
        )
    ).scalars().all()

    if existing_assignments:
        return existing_assignments

    if not required_trades:

        required_trades = [
            {
                "trade": (
                    maintenance_request.category
                    or ""
                ),
                "reason": (
                    "Maintenance request category"
                )
            }
        ]

    workers = db.session.execute(
        select(User).where(
            User.organisation_id
            == organisation_id,
            User.role == "worker",
            User.is_active.is_(True)
        )
    ).scalars().all()

    if not workers:

        location = get_property_location(
            maintenance_request
        )

        try:

            external_candidates = (
                search_external_workers(
                    maintenance_request.id,
                    required_trades,
                    location
                )
            )

            save_external_candidates(
                maintenance_request.id,
                external_candidates
            )

        except Exception as exc:

            print(
                "\n========== GEMINI CONTRACTOR DISCOVERY ERROR ==========",
                flush=True
            )

            print(
                f"Error: {exc!r}",
                flush=True
            )

            traceback.print_exc()

            print(
                "========================================================\n",
                flush=True
            )

        return []

    ranked_workers = _rank_internal_workers(
        maintenance_request,
        required_trades,
        workers
    )

    assignments = []
    used_worker_ids = set()
    missing_trades = []

    for trade_info in required_trades:

        required_trade = (
            trade_info.get(
                "trade",
                ""
            )
            if isinstance(
                trade_info,
                dict
            )
            else str(
                trade_info
            )
        )

        required_trade = (
            required_trade.strip()
        )

        if not required_trade:
            continue

        trade_lower = (
            required_trade.lower()
        )

        available_workers = [
            result
            for result in ranked_workers
            if result["worker"].id
            not in used_worker_ids
        ]

        trade_matches = []

        for result in available_workers:

            speciality = _safe_string(
                result["worker"].speciality
            ).lower()

            if (
                trade_lower in speciality
                or speciality in trade_lower
            ):
                trade_matches.append(
                    result
                )

        if trade_matches:

            best_result = max(
                trade_matches,
                key=lambda result: result["score"]
            )

        elif available_workers:

            best_result = max(
                available_workers,
                key=lambda result: result["score"]
            )

        else:

            missing_trades.append(
                trade_info
            )

            continue

        if best_result["score"] < 0.7:

            missing_trades.append(
                trade_info
            )

            continue

        worker = best_result["worker"]

        assignment = TaskAssignment(
            maintenance_request_id=(
                maintenance_request.id
            ),
            user_id=worker.id,
            assignment_method="ai",
            score=best_result["score"]
        )

        db.session.add(
            assignment
        )

        assignments.append(
            assignment
        )

        used_worker_ids.add(
            worker.id
        )

    if missing_trades:

        location = get_property_location(
            maintenance_request
        )

        try:

            external_candidates = (
                search_external_workers(
                    maintenance_request.id,
                    missing_trades,
                    location
                )
            )

            save_external_candidates(
                maintenance_request.id,
                external_candidates
            )

        except Exception as exc:

            print(
                "\n========== GEMINI CONTRACTOR DISCOVERY ERROR ==========",
                flush=True
            )

            print(
                f"Error: {exc!r}",
                flush=True
            )

            traceback.print_exc()

            print(
                "========================================================\n",
                flush=True
            )

    return assignments