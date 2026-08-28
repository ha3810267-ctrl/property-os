from datetime import datetime, timezone

from backend.database import db

from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)

from backend.models.maintenance_request import (
    MaintenanceRequest
)

from backend.services.gemini_contractor_response import (
    analyse_contractor_response
)

from backend.services.external_worker_ranking import (
    rank_external_workers
)

from backend.services.ai_maintenance import (
    analyse_maintenance_request
)


def process_contractor_response(
    candidate: ExternalWorkerCandidate,
    maintenance_request: MaintenanceRequest,
    contractor_response: str
):
    """
    Process a contractor response.

    Full flow:

        contractor email response
                    |
                    v
        Gemini analyses response
                    |
                    +--> summary
                    +--> response quality
                    +--> quoted price
                    +--> estimated start
                    +--> availability
                    |
                    v
        update contractor candidate
                    |
                    v
        determine required trades
                    |
                    v
        load all candidates
                    |
                    v
        re-rank candidates
                    |
                    v
        persist updated state
                    |
                    v
        frontend receives updated information

    The contractor is NEVER automatically selected.
    """

    # ============================================================
    # VALIDATION
    # ============================================================

    if candidate is None:
        raise ValueError(
            "Contractor candidate is required"
        )

    if maintenance_request is None:
        raise ValueError(
            "Maintenance request is required"
        )

    if not isinstance(contractor_response, str):
        raise ValueError(
            "Contractor response must be a string"
        )

    contractor_response = (
        contractor_response.strip()
    )

    if not contractor_response:
        raise ValueError(
            "Contractor response is required"
        )

    # Make sure the candidate actually belongs to
    # this maintenance request

    if (
        candidate.maintenance_request_id
        != maintenance_request.id
    ):
        raise ValueError(
            "Contractor candidate does not belong "
            "to this maintenance request"
        )

    # ============================================================
    # GEMINI RESPONSE ANALYSIS
    # ============================================================

    try:

        analysis = analyse_contractor_response(
            contractor_name=candidate.name,
            contractor_email=candidate.email,
            maintenance_description=(
                maintenance_request.description
            ),
            contractor_response=contractor_response
        )

    except Exception as exc:

        db.session.rollback()

        raise RuntimeError(
            f"Could not analyse contractor response: {exc}"
        ) from exc

    if not isinstance(analysis, dict):
        db.session.rollback()

        raise RuntimeError(
            "Gemini returned an invalid contractor analysis"
        )

    # ============================================================
    # VALIDATE GEMINI RESULT
    # ============================================================

    response_quality = analysis.get(
        "response_quality"
    )

    summary = analysis.get(
        "summary"
    )

    quoted_price = analysis.get(
        "quoted_price"
    )

    estimated_start = analysis.get(
        "estimated_start"
    )

    can_take_job = analysis.get(
        "can_take_job"
    )

    if not response_quality:
        response_quality = "unclear"

    if not summary:
        summary = (
            "Contractor response received but "
            "no summary was generated."
        )

    # ============================================================
    # NORMALISE AVAILABILITY
    # ============================================================

    if can_take_job not in (
        True,
        False,
        None
    ):
        can_take_job = None

    # ============================================================
    # UPDATE CONTRACTOR RESPONSE STATE
    # ============================================================

    now = datetime.now(
        timezone.utc
    )

    candidate.response_received_at = now

    candidate.last_message = (
        contractor_response
    )

    candidate.response_quality = (
        response_quality
    )

    candidate.gemini_summary = (
        summary
    )

    candidate.quoted_price = (
        quoted_price
    )

    candidate.estimated_start = (
        estimated_start
    )

    # Store the actual contractor availability
    # if the model supports it

    if hasattr(
        candidate,
        "can_take_job"
    ):
        candidate.can_take_job = (
            can_take_job
        )

    # ============================================================
    # UPDATE CONTACT STATUS
    # ============================================================

    if can_take_job is False:

        candidate.contact_status = (
            "unavailable"
        )

    elif can_take_job is True:

        candidate.contact_status = (
            "response_received"
        )

    else:

        candidate.contact_status = (
            "response_received"
        )

    candidate.updated_at = now

    # ============================================================
    # DETERMINE REQUIRED TRADES
    # ============================================================

    try:

        ai_result = analyse_maintenance_request(
            maintenance_request.description
        )

    except Exception as exc:

        db.session.rollback()

        raise RuntimeError(
            "Could not determine required "
            f"contractor trades: {exc}"
        ) from exc

    if not isinstance(ai_result, dict):

        db.session.rollback()

        raise RuntimeError(
            "Maintenance AI returned an invalid result"
        )

    required_trades = ai_result.get(
        "required_trades",
        []
    )

    if not isinstance(
        required_trades,
        list
    ) or not required_trades:

        db.session.rollback()

        raise RuntimeError(
            "Could not determine required "
            "contractor trades"
        )

    # ============================================================
    # LOAD ALL CONTRACTOR CANDIDATES
    # ============================================================

    candidates = db.session.execute(
        db.select(
            ExternalWorkerCandidate
        )
        .where(
            ExternalWorkerCandidate
            .maintenance_request_id
            == maintenance_request.id
        )
    ).scalars().all()

    if not candidates:

        db.session.rollback()

        raise RuntimeError(
            "No contractor candidates exist for "
            "this maintenance request"
        )

    # ============================================================
    # RE-RANK ALL CONTRACTORS
    # ============================================================

    try:

        ranked_candidates = rank_external_workers(
            maintenance_description=(
                maintenance_request.description
            ),
            required_trades=required_trades,
            candidates=candidates
        )

    except Exception as exc:

        db.session.rollback()

        raise RuntimeError(
            f"Could not re-rank contractor candidates: {exc}"
        ) from exc

    # ============================================================
    # PERSIST RANKING RESULTS
    # ============================================================

    #
    # IMPORTANT
    #
    # rank_external_workers may return the candidates
    # in ranked order, but we also need to make sure
    # the ranking information is actually persisted
    # to the database.
    #

    for position, ranked_candidate in enumerate(
        ranked_candidates,
        start=1
    ):

        if hasattr(
            ranked_candidate,
            "rank"
        ):
            ranked_candidate.rank = position

        if hasattr(
            ranked_candidate,
            "updated_at"
        ):
            ranked_candidate.updated_at = now

    # ============================================================
    # SAVE EVERYTHING AS ONE TRANSACTION
    # ============================================================

    try:

        db.session.commit()

    except Exception as exc:

        db.session.rollback()

        raise RuntimeError(
            f"Could not save contractor response: {exc}"
        ) from exc

    # ============================================================
    # RETURN UPDATED DATA
    # ============================================================

    return {
        "candidate": candidate,
        "analysis": {
            "response_quality": response_quality,
            "summary": summary,
            "quoted_price": quoted_price,
            "estimated_start": estimated_start,
            "can_take_job": can_take_job
        },
        "required_trades": required_trades,
        "ranked_candidates": ranked_candidates
    }