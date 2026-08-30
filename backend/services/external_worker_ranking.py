
from datetime import datetime, timezone

from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)


# ============================================================
# RANKING WEIGHTS
# ============================================================

# Trade relevance
TRADE_WEIGHT = 0.30

# Contractor reputation
RATING_WEIGHT = 0.25
REVIEWS_WEIGHT = 0.15

# Availability
AVAILABILITY_WEIGHT = 0.25

# Small price signal
PRICE_WEIGHT = 0.05


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

    # Missing rating is neutral
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

    The score is capped so extremely large review counts
    do not completely dominate the ranking.
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
    Estimate availability using information actually present
    on the discovered contractor.

    Discovery alone does NOT mean the contractor is available.

    If no availability information exists, the contractor
    receives a neutral score.
    """

    availability = str(
        getattr(
            candidate,
            "availability",
            ""
        ) or ""
    ).strip().lower()

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

    # Unknown wording
    return 0.50


# ============================================================
# PRICE SCORE
# ============================================================

def _price_score(
    candidate
):
    """
    Give a small ranking signal to contractors with a quote.

    Price is intentionally not a major ranking factor.
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

    # A known quote receives a small positive signal.
    # Actual price comparison can be added later when
    # multiple quotes exist for the same request.
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

    Ranking considers ONLY:

        trade relevance
        contractor rating
        review confidence
        availability
        quote information

    There is deliberately no contact or response logic here.
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

    price_score = _price_score(
        candidate
    )

    score = (
        trade_score * TRADE_WEIGHT
        + rating_score * RATING_WEIGHT
        + review_score * REVIEWS_WEIGHT
        + availability_score * AVAILABILITY_WEIGHT
        + price_score * PRICE_WEIGHT
    )

    # --------------------------------------------------------
    # Unavailable contractors
    # --------------------------------------------------------

    availability = str(
        getattr(
            candidate,
            "availability",
            ""
        ) or ""
    ).strip().lower()

    unavailable_terms = (
        "unavailable",
        "not available",
        "fully booked",
        "booked up",
        "no availability",
        "not taking work",
        "not taking jobs"
    )

    if any(
        term in availability
        for term in unavailable_terms
    ):
        score *= 0.10

    return _clamp(
        score
    )


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

    This function contains NO contractor response or
    contact-status messaging.
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

    Updates:

        match_score
        match_reason
        ranking_updated_at
        updated_at

    The function NEVER contacts contractors.

    The function NEVER sends or receives messages.

    The function NEVER selects a contractor.

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
            # Availability first
            _availability_score(
                candidate
            ),

            # Overall match score
            getattr(
                candidate,
                "match_score",
                0
            ),

            # Rating
            _rating_score(
                candidate
            ),

            # Reviews
            _review_score(
                candidate
            ),

            # Trade
            _trade_score(
                candidate,
                required_trades
            )
        )

    scored_candidates.sort(
        key=ranking_key,
        reverse=True
    )

    return scored_candidates

