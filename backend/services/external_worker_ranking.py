
from datetime import datetime, timezone
import re

from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)


# ============================================================
# RANKING WEIGHTS
# ============================================================

# Trade relevance
TRADE_WEIGHT = 0.25

# Geographic relevance
LOCATION_WEIGHT = 0.25

# Contractor reputation
RATING_WEIGHT = 0.20
REVIEWS_WEIGHT = 0.10

# Availability
AVAILABILITY_WEIGHT = 0.15

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


def _normalise_location_text(
    value
):
    """
    Normalise location text for comparison.

    This does NOT invent or geocode locations.
    """

    if value is None:
        return ""

    value = str(
        value
    ).strip().lower()

    if not value:
        return ""

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    return value


def _location_tokens(
    value
):
    """
    Extract useful location words.

    Very short/common words are ignored so that generic
    words do not artificially increase the location score.
    """

    value = _normalise_location_text(
        value
    )

    if not value:
        return set()

    ignored = {
        "the",
        "and",
        "of",
        "in",
        "on",
        "at",
        "uk",
        "united",
        "kingdom",
        "england",
        "road",
        "street",
        "lane",
        "avenue",
        "close",
        "court",
        "place",
    }

    return {
        token
        for token in value.split()
        if len(token) >= 3
        and token not in ignored
    }


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

    if candidate_trade in normalised_trades:
        return 1.0

    for trade in normalised_trades:

        if (
            trade in candidate_trade
            or candidate_trade in trade
        ):
            return 0.9

    return 0.2


# ============================================================
# LOCATION SCORE
# ============================================================

def _location_score(
    candidate,
    target_location
):
    """
    Score how closely the contractor's stated location
    matches the property's target location.

    This uses ONLY location information actually present
    on the candidate and the maintenance request.

    It does not invent distances or coordinates.

    Strongest matches:

        exact location text
        location contained within target
        target contained within contractor location
        multiple meaningful location tokens

    Unknown locations receive a neutral score rather than
    being automatically penalised.
    """

    target = _normalise_location_text(
        target_location
    )

    candidate_location = _normalise_location_text(
        getattr(
            candidate,
            "location",
            None
        )
    )

    if not target:
        return 0.50

    if not candidate_location:
        return 0.35

    # Exact match
    if candidate_location == target:
        return 1.0

    # One location fully contains the other
    if (
        candidate_location in target
        or target in candidate_location
    ):
        return 0.90

    target_tokens = _location_tokens(
        target
    )

    candidate_tokens = _location_tokens(
        candidate_location
    )

    if not target_tokens or not candidate_tokens:
        return 0.35

    overlap = (
        target_tokens
        & candidate_tokens
    )

    overlap_count = len(
        overlap
    )

    target_count = len(
        target_tokens
    )

    candidate_count = len(
        candidate_tokens
    )

    # Strong overlap
    if overlap_count >= 3:
        return 0.90

    if overlap_count == 2:
        return 0.80

    if overlap_count == 1:
        # A single meaningful matching town/area/postcode
        # is still useful evidence.
        if (
            target_count <= 2
            or candidate_count <= 2
        ):
            return 0.75

        return 0.65

    # No textual overlap
    return 0.20


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

    if not availability:
        return 0.50

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

    return 0.60


# ============================================================
# OVERALL MATCH SCORE
# ============================================================

def calculate_external_worker_score(
    candidate,
    required_trades=None,
    target_location=None
):
    """
    Calculate the contractor's overall match score.

    Score is between 0 and 1.

    Ranking considers:

        trade relevance
        geographic relevance
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

    location_score = _location_score(
        candidate,
        target_location
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
        + location_score * LOCATION_WEIGHT
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
    required_trades=None,
    target_location=None
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

    location_score = _location_score(
        candidate,
        target_location
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
    # Location
    # --------------------------------------------------------

    if location_score >= 0.90:

        reasons.append(
            "very close location match"
        )

    elif location_score >= 0.75:

        reasons.append(
            "strong local match"
        )

    elif location_score >= 0.60:

        reasons.append(
            "nearby service area"
        )

    elif location_score <= 0.25:

        reasons.append(
            "wider service area"
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
    candidates,
    target_location=None
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
            required_trades=required_trades,
            target_location=target_location
        )

        reason = build_match_reason(
            candidate=candidate,
            score=score,
            required_trades=required_trades,
            target_location=target_location
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
            # Overall score is the primary ranking.
            getattr(
                candidate,
                "match_score",
                0
            ),

            # Location is the first tie-breaker.
            _location_score(
                candidate,
                target_location
            ),

            # Availability
            _availability_score(
                candidate
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