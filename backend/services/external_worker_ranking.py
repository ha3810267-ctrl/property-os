
from datetime import datetime, timezone
from typing import Iterable

from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)


# ============================================================
# RANKING WEIGHTS
# ============================================================

# Trade relevance is important because the contractor
# must actually be suitable for the maintenance job.

TRADE_WEIGHT = 0.20

# Contractor reputation.

RATING_WEIGHT = 0.20
REVIEWS_WEIGHT = 0.10

# Availability is important before and after outreach.

AVAILABILITY_WEIGHT = 0.20

# Contractor response information becomes increasingly
# important once responses start arriving.

RESPONSE_WEIGHT = 0.30


# ============================================================
# HELPERS
# ============================================================

def _safe_float(
    value,
    default=0.0
):
    """
    Safely convert a value to float.
    """

    try:

        if value is None:
            return default

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return default


def _clamp(
    value,
    minimum=0.0,
    maximum=1.0
):
    """
    Keep a score between 0 and 1.
    """

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


# ============================================================
# TRADE SCORE
# ============================================================

def _trade_score(
    candidate,
    required_trades
):
    """
    Calculate how closely the contractor's trade matches
    the trades required by the maintenance request.
    """

    if not required_trades:
        return 0.5

    candidate_trade = str(
        getattr(
            candidate,
            "trade",
            ""
        ) or ""
    ).strip().lower()

    if not candidate_trade:
        return 0.5

    normalised_trades = []

    for trade in required_trades:

        if trade is None:
            continue

        trade = str(
            trade
        ).strip().lower()

        if trade:
            normalised_trades.append(
                trade
            )

    if not normalised_trades:
        return 0.5

    # Exact match

    if candidate_trade in normalised_trades:
        return 1.0

    # Partial match

    for trade in normalised_trades:

        if (
            trade in candidate_trade
            or candidate_trade in trade
        ):
            return 0.9

    # No obvious trade match

    return 0.2


# ============================================================
# RATING SCORE
# ============================================================

def _rating_score(
    candidate
):
    """
    Convert a 0-5 contractor rating into 0-1.
    """

    rating = _safe_float(
        getattr(
            candidate,
            "rating",
            None
        )
    )

    if rating <= 0:
        return 0.5

    return _clamp(
        rating / 5.0
    )


# ============================================================
# REVIEW SCORE
# ============================================================

def _review_score(
    candidate
):
    """
    Give contractors with more reviews more confidence.

    This is deliberately capped so a contractor with
    thousands of reviews does not completely dominate
    contractors with strong ratings and availability.
    """

    reviews = _safe_float(
        getattr(
            candidate,
            "review_count",
            None
        )
    )

    if reviews <= 0:
        return 0.25

    return _clamp(
        reviews / 100.0
    )


# ============================================================
# AVAILABILITY SCORE
# ============================================================

def _availability_score(
    candidate
):
    """
    Estimate availability using the information stored
    on the candidate.

    This works before and after contractor outreach.

    Important:

    We do NOT assume that a contractor is available just
    because they were discovered.

    Discovery therefore receives a neutral score unless
    the source supplied meaningful availability information.
    """

    availability = str(
        getattr(
            candidate,
            "availability",
            ""
        ) or ""
    ).strip().lower()

    contact_status = str(
        getattr(
            candidate,
            "contact_status",
            ""
        ) or ""
    ).strip().lower()

    response_quality = str(
        getattr(
            candidate,
            "response_quality",
            ""
        ) or ""
    ).strip().lower()

    # --------------------------------------------------------
    # Explicit response indicating unavailability
    # --------------------------------------------------------

    if (
        contact_status == "unavailable"
        or response_quality == "unavailable"
    ):
        return 0.0

    # --------------------------------------------------------
    # Contractor has responded but availability is unclear
    # --------------------------------------------------------

    if contact_status == "response_received":

        if response_quality == "good":
            return 0.85

        if response_quality == "poor":
            return 0.55

        return 0.60

    # --------------------------------------------------------
    # Contractor has been contacted but has not responded
    # --------------------------------------------------------

    if contact_status in {
        "contacted",
        "email_sent"
    }:

        # We do not know whether they can take the job.
        return 0.40

    # --------------------------------------------------------
    # No availability information
    # --------------------------------------------------------

    if not availability:
        return 0.50

    # --------------------------------------------------------
    # Explicit unavailable language
    # --------------------------------------------------------

    unavailable_terms = (
        "unavailable",
        "not available",
        "fully booked",
        "booked up",
        "busy",
        "cannot",
        "can't",
        "unable",
        "no availability",
        "not taking work",
        "not taking jobs"
    )

    if any(
        term in availability
        for term in unavailable_terms
    ):
        return 0.0

    # --------------------------------------------------------
    # Strong availability language
    # --------------------------------------------------------

    strong_available_terms = (
        "same day",
        "today",
        "tomorrow",
        "immediate",
        "immediately",
        "available now",
        "available today",
        "available tomorrow"
    )

    if any(
        term in availability
        for term in strong_available_terms
    ):
        return 1.0

    # --------------------------------------------------------
    # General availability language
    # --------------------------------------------------------

    available_terms = (
        "available",
        "this week",
        "next week",
        "accepting work",
        "taking work",
        "taking jobs"
    )

    if any(
        term in availability
        for term in available_terms
    ):
        return 0.85

    return 0.50


# ============================================================
# RESPONSE SCORE
# ============================================================

def _response_score(
    candidate
):
    """
    Score the usefulness of the contractor's response.

    This is the main dynamic component of the ranking.

    A contractor who provides a clear response and can
    take the job receives a strong score.

    A contractor who explicitly cannot take the job
    receives zero.

    Contractors who have not responded retain a lower
    neutral score.
    """

    response_received = getattr(
        candidate,
        "response_received_at",
        None
    )

    response_quality = str(
        getattr(
            candidate,
            "response_quality",
            ""
        ) or ""
    ).strip().lower()

    contact_status = str(
        getattr(
            candidate,
            "contact_status",
            ""
        ) or ""
    ).strip().lower()

    # --------------------------------------------------------
    # Explicitly unavailable
    # --------------------------------------------------------

    if (
        contact_status == "unavailable"
        or response_quality == "unavailable"
    ):
        return 0.0

    # --------------------------------------------------------
    # No response yet
    # --------------------------------------------------------

    if response_received is None:

        if contact_status in {
            "contacted",
            "email_sent"
        }:
            return 0.30

        return 0.20

    # --------------------------------------------------------
    # Response received
    # --------------------------------------------------------

    if response_quality == "good":
        return 1.0

    if response_quality == "poor":
        return 0.45

    if response_quality == "unclear":
        return 0.60

    return 0.55


# ============================================================
# PRICE SCORE
# ============================================================

def _price_score(
    candidate
):
    """
    Price is deliberately NOT a major ranking factor.

    A cheap contractor should not automatically beat a
    more suitable contractor.

    For now:

        price present -> neutral positive signal
        price missing  -> neutral

    A more advanced version can compare contractor quotes
    against the distribution of quotes received for the
    same maintenance request.
    """

    quoted_price = getattr(
        candidate,
        "quoted_price",
        None
    )

    if quoted_price is None:
        return 0.5

    quoted_price = _safe_float(
        quoted_price,
        default=0.0
    )

    if quoted_price <= 0:
        return 0.5

    return 0.60


# ============================================================
# OVERALL MATCH SCORE
# ============================================================

def calculate_external_worker_score(
    candidate,
    required_trades=None
):
    """
    Calculate the contractor's overall match score.

    Score is between 0 and 1.

    Ranking considers:

        trade relevance
        contractor rating
        review confidence
        availability
        contractor response
        quote information

    Contractor response information dynamically affects
    the ranking after outreach.
    """

    required_trades = (
        required_trades or []
    )

    trade_score = _trade_score(
        candidate,
        required_trades
    )

    rating_score = _rating_score(
        candidate
    )

    review_score = _review_score(
        candidate
    )

    availability_score = (
        _availability_score(
            candidate
        )
    )

    response_score = _response_score(
        candidate
    )

    price_score = _price_score(
        candidate
    )

    # ========================================================
    # BASE SCORE
    # ========================================================

    score = (
        trade_score * TRADE_WEIGHT
        + rating_score * RATING_WEIGHT
        + review_score * REVIEWS_WEIGHT
        + availability_score * AVAILABILITY_WEIGHT
        + response_score * RESPONSE_WEIGHT
    )

    # Price currently acts only as a very small tie-break
    # rather than a major factor.

    score += (
        (price_score - 0.5)
        * 0.05
    )

    # ========================================================
    # UNAVAILABLE CONTRACTORS
    # ========================================================

    if (
        getattr(
            candidate,
            "contact_status",
            None
        )
        == "unavailable"
    ):

        score *= 0.10

    if (
        getattr(
            candidate,
            "response_quality",
            None
        )
        == "unavailable"
    ):

        score *= 0.10

    score = _clamp(
        score
    )

    return score


# ============================================================
# MATCH REASON
# ============================================================

def build_match_reason(
    candidate,
    score,
    required_trades=None
):
    """
    Build a human-readable explanation for the ranking.

    This explanation is returned to the frontend.
    """

    required_trades = (
        required_trades or []
    )

    reasons = []

    trade_score = _trade_score(
        candidate,
        required_trades
    )

    rating_score = _rating_score(
        candidate
    )

    availability_score = (
        _availability_score(
            candidate
        )
    )

    response_score = _response_score(
        candidate
    )

    # --------------------------------------------------------
    # Trade
    # --------------------------------------------------------

    if trade_score >= 0.9:

        reasons.append(
            "strong trade match"
        )

    elif trade_score >= 0.7:

        reasons.append(
            "relevant trade"
        )

    # --------------------------------------------------------
    # Rating
    # --------------------------------------------------------

    if rating_score >= 0.85:

        reasons.append(
            "strong rating"
        )

    elif rating_score >= 0.65:

        reasons.append(
            "good rating"
        )

    # --------------------------------------------------------
    # Availability
    # --------------------------------------------------------

    if availability_score >= 0.90:

        reasons.append(
            "strong availability"
        )

    elif availability_score >= 0.75:

        reasons.append(
            "appears available"
        )

    elif availability_score <= 0.10:

        reasons.append(
            "currently unavailable"
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    if response_score >= 0.90:

        reasons.append(
            "clear contractor response"
        )

    elif response_score >= 0.60:

        reasons.append(
            "contractor response received"
        )

    elif response_score <= 0.30:

        reasons.append(
            "awaiting contractor response"
        )

    # --------------------------------------------------------
    # Quote
    # --------------------------------------------------------

    if getattr(
        candidate,
        "quoted_price",
        None
    ) is not None:

        reasons.append(
            "quote provided"
        )

    # --------------------------------------------------------
    # Response quality
    # --------------------------------------------------------

    response_quality = str(
        getattr(
            candidate,
            "response_quality",
            ""
        ) or ""
    ).lower()

    if response_quality == "good":

        reasons.append(
            "useful response information"
        )

    elif response_quality == "poor":

        reasons.append(
            "limited response information"
        )

    elif response_quality == "unavailable":

        reasons.append(
            "contractor cannot take the job"
        )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if not reasons:

        reasons.append(
            "potential match based on available information"
        )

    return (
        f"{int(round(score * 100))}% match — "
        + ", ".join(reasons)
    )


# ============================================================
# RANK CONTRACTORS
# ============================================================

def rank_external_workers(
    maintenance_description,
    required_trades,
    candidates
):

    """
    Rank all external contractor candidates.

    The function updates:

        match_score
        match_reason
        ranking_updated_at
        updated_at

    and returns candidates sorted from strongest match
    to weakest match.

    IMPORTANT:

    This function NEVER selects a contractor.

    Selection remains a manager action.
    """

    if not isinstance(
        maintenance_description,
        str
    ) or not maintenance_description.strip():

        raise ValueError(
            "Maintenance description is required"
        )

    if not isinstance(
        required_trades,
        list
    ):

        raise ValueError(
            "required_trades must be a list"
        )

    candidates = list(
        candidates or []
    )

    if not candidates:
        return []

    scored_candidates = []

    for candidate in candidates:

        if not isinstance(
            candidate,
            ExternalWorkerCandidate
        ):
            continue

        score = calculate_external_worker_score(
            candidate=candidate,
            required_trades=required_trades
        )

        reason = build_match_reason(
            candidate=candidate,
            score=score,
            required_trades=required_trades
        )

        candidate.match_score = score

        candidate.match_reason = reason

        candidate.ranking_updated_at = (
            datetime.now(
                timezone.utc
            )
        )

        candidate.updated_at = (
            datetime.now(
                timezone.utc
            )
        )

        scored_candidates.append(
            candidate
        )

    # ========================================================
    # SORT
    # ========================================================

    def ranking_key(
        candidate
    ):

        return (
            # Available/response candidates first
            _availability_score(
                candidate
            ),

            # Actual contractor response next
            _response_score(
                candidate
            ),

            # Overall match score
            getattr(
                candidate,
                "match_score",
                0
            ),

            # Rating as final tie-break
            _rating_score(
                candidate
            ),

            # Reviews as final tie-break
            _review_score(
                candidate
            )
        )

    scored_candidates.sort(
        key=ranking_key,
        reverse=True
    )

    return scored_candidates

