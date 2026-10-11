
from datetime import datetime, timezone
import re

from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate,
)


# ============================================================
# RANKING WEIGHTS
# ============================================================

SERVICE_WEIGHT = 0.30
LOCATION_WEIGHT = 0.25
RATING_WEIGHT = 0.20
REVIEWS_WEIGHT = 0.10
AVAILABILITY_WEIGHT = 0.10
PRICE_WEIGHT = 0.05

# Backwards compatibility with existing imports.
TRADE_WEIGHT = SERVICE_WEIGHT


# ============================================================
# HELPERS
# ============================================================

def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))


def _normalise_text(value):
    if value is None:
        return ""

    value = str(value).strip().lower()

    if not value:
        return ""

    value = value.replace("&", " and ")

    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _normalise_location_text(value):
    return _normalise_text(value)


def _location_tokens(value):
    value = _normalise_location_text(value)

    if not value:
        return set()

    ignored = {
        "the", "and", "of", "in", "on", "at",
        "uk", "united", "kingdom", "england",
        "road", "street", "lane", "avenue",
        "close", "court", "place",
    }

    return {
        token
        for token in value.split()
        if len(token) >= 3 and token not in ignored
    }


def _extract_service_requirements(required_services):
    """
    Accept the existing required_trades list as well as
    arbitrary service requirements.

    Supported examples:
        ["plumber", "electrician"]

        [
            {
                "trade": "photographer",
                "reason": "Event photography"
            }
        ]

    No fixed service-category list is used.
    """
    requirements = []

    for item in required_services or []:
        if isinstance(item, dict):
            service = (
                item.get("trade")
                or item.get("service")
                or item.get("category")
                or ""
            )

            reason = (
                item.get("reason")
                or item.get("description")
                or ""
            )

            service = _normalise_text(service)
            reason = _normalise_text(reason)

            if service:
                requirements.append({
                    "service": service,
                    "reason": reason,
                })

        else:
            service = _normalise_text(item)

            if service:
                requirements.append({
                    "service": service,
                    "reason": "",
                })

    return requirements


# ============================================================
# SERVICE RELEVANCE
# ============================================================

def _service_score(candidate, required_services):
    """
    Estimate semantic service relevance using the available
    service labels and reasons.

    This is deliberately generic: it does not assume every
    provider is a property-maintenance contractor.

    Note:
    Text similarity is an estimate, not proof of competence.
    """
    requirements = _extract_service_requirements(
        required_services
    )

    if not requirements:
        return 0.50

    candidate_service = _normalise_text(
        getattr(candidate, "trade", None)
    )

    if not candidate_service:
        return 0.30

    candidate_tokens = set(candidate_service.split())

    best_score = 0.0

    for requirement in requirements:
        service = requirement["service"]
        reason = requirement["reason"]

        service_tokens = set(service.split())
        reason_tokens = set(reason.split())

        # Exact service label.
        if candidate_service == service:
            best_score = max(best_score, 1.0)
            continue

        # One label is contained in the other.
        if service in candidate_service or candidate_service in service:
            best_score = max(best_score, 0.90)
            continue

        # Compare the candidate label with the requested service.
        if service_tokens:
            overlap = candidate_tokens & service_tokens

            if overlap:
                precision = len(overlap) / max(
                    len(candidate_tokens), 1
                )
                recall = len(overlap) / max(
                    len(service_tokens), 1
                )

                if precision + recall:
                    f1 = (
                        2 * precision * recall
                        / (precision + recall)
                    )
                else:
                    f1 = 0.0

                best_score = max(
                    best_score,
                    min(0.85, f1),
                )

        # The reason can contain useful context, but it is
        # not treated as definitive proof of a service match.
        if reason_tokens:
            overlap = candidate_tokens & reason_tokens

            if overlap:
                coverage = len(overlap) / max(
                    len(reason_tokens), 1
                )

                best_score = max(
                    best_score,
                    min(0.70, coverage),
                )

    # A label with no meaningful overlap is a weak match,
    # rather than an automatic rejection.
    return _clamp(max(0.20, best_score))


def _trade_score(candidate, required_trades):
    """
    Backwards-compatible alias used by existing code.
    """
    return _service_score(candidate, required_trades)


# ============================================================
# LOCATION SCORE
# ============================================================

def _location_score(candidate, target_location):
    target = _normalise_location_text(target_location)

    candidate_location = _normalise_location_text(
        getattr(candidate, "location", None)
    )

    if not target:
        return 0.50

    if not candidate_location:
        return 0.35

    if candidate_location == target:
        return 1.0

    if (
        candidate_location in target
        or target in candidate_location
    ):
        return 0.90

    target_tokens = _location_tokens(target)
    candidate_tokens = _location_tokens(candidate_location)

    if not target_tokens or not candidate_tokens:
        return 0.35

    overlap = target_tokens & candidate_tokens

    if len(overlap) >= 3:
        return 0.90

    if len(overlap) == 2:
        return 0.80

    if len(overlap) == 1:
        if len(target_tokens) <= 2 or len(candidate_tokens) <= 2:
            return 0.75

        return 0.65

    return 0.20


# ============================================================
# RATING SCORE
# ============================================================

def _rating_score(candidate):
    rating = _safe_float(
        getattr(candidate, "rating", None)
    )

    if rating <= 0:
        return 0.50

    return _clamp(rating / 5.0)


# ============================================================
# REVIEW SCORE
# ============================================================

def _review_score(candidate):
    reviews = _safe_float(
        getattr(candidate, "review_count", None)
    )

    if reviews <= 0:
        return 0.25

    return _clamp(reviews / 100.0)


# ============================================================
# AVAILABILITY SCORE
# ============================================================

def _availability_score(candidate):
    availability = _normalise_text(
        getattr(candidate, "availability", None)
    )

    if not availability:
        return 0.50

    unavailable_terms = (
        "unavailable",
        "not available",
        "fully booked",
        "booked up",
        "no availability",
        "not taking work",
        "not taking jobs",
        "unable to take work",
    )

    if any(term in availability for term in unavailable_terms):
        return 0.0

    strong_available_terms = (
        "same day",
        "today",
        "tomorrow",
        "immediate",
        "immediately",
        "available now",
        "available today",
        "available tomorrow",
    )

    if any(term in availability for term in strong_available_terms):
        return 1.0

    available_terms = (
        "available",
        "this week",
        "next week",
        "accepting work",
        "taking work",
        "taking jobs",
    )

    if any(term in availability for term in available_terms):
        return 0.85

    return 0.50


# ============================================================
# PRICE SCORE
# ============================================================

def _price_score(candidate):
    quoted_price = getattr(candidate, "quoted_price", None)

    if quoted_price is None:
        return 0.50

    quoted_price = _safe_float(quoted_price, default=0.0)

    if quoted_price <= 0:
        return 0.50

    # A quote exists, but without a comparable budget or other
    # quotes, a low-price ranking advantage cannot be justified.
    return 0.60


# ============================================================
# OVERALL MATCH SCORE
# ============================================================

def calculate_external_worker_score(
    candidate,
    required_trades=None,
    target_location=None,
):
    """
    Return a score between 0 and 1.

    The legacy required_trades parameter now represents
    arbitrary required services/provider types.
    """
    required_trades = required_trades or []

    service_score = _service_score(
        candidate,
        required_trades,
    )

    location_score = _location_score(
        candidate,
        target_location,
    )

    rating_score = _rating_score(candidate)
    review_score = _review_score(candidate)

    availability_score = _availability_score(candidate)
    price_score = _price_score(candidate)

    score = (
        service_score * SERVICE_WEIGHT
        + location_score * LOCATION_WEIGHT
        + rating_score * RATING_WEIGHT
        + review_score * REVIEWS_WEIGHT
        + availability_score * AVAILABILITY_WEIGHT
        + price_score * PRICE_WEIGHT
    )

    availability = _normalise_text(
        getattr(candidate, "availability", None)
    )

    unavailable_terms = (
        "unavailable",
        "not available",
        "fully booked",
        "booked up",
        "no availability",
        "not taking work",
        "not taking jobs",
        "unable to take work",
    )

    if any(term in availability for term in unavailable_terms):
        score *= 0.10

    return _clamp(score)


# ============================================================
# MATCH REASON
# ============================================================

def build_match_reason(
    candidate,
    score,
    required_trades=None,
    target_location=None,
):
    """
    Explain the ranking without claiming that availability
    or professional qualifications have been independently
    confirmed.
    """
    required_trades = required_trades or []

    reasons = []

    service_score = _service_score(
        candidate,
        required_trades,
    )

    location_score = _location_score(
        candidate,
        target_location,
    )

    rating_score = _rating_score(candidate)
    availability_score = _availability_score(candidate)

    if service_score >= 0.90:
        reasons.append("strong service match")
    elif service_score >= 0.65:
        reasons.append("relevant service")
    else:
        reasons.append("service match needs checking")

    if location_score >= 0.90:
        reasons.append("strong location match")
    elif location_score >= 0.75:
        reasons.append("good local match")
    elif location_score >= 0.60:
        reasons.append("some location overlap")
    elif location_score <= 0.25:
        reasons.append("wider service area")

    if rating_score >= 0.85:
        reasons.append("strong rating")
    elif rating_score >= 0.65:
        reasons.append("good rating")

    if availability_score >= 0.90:
        reasons.append("availability information looks positive")
    elif availability_score >= 0.75:
        reasons.append("availability information provided")
    elif availability_score <= 0.10:
        reasons.append("reported unavailable")

    if getattr(candidate, "quoted_price", None) is not None:
        reasons.append("quote information provided")

    return (
        f"{int(round(score * 100))}% match — "
        + ", ".join(reasons)
    )


# ============================================================
# RANK PROVIDERS
# ============================================================

def rank_external_workers(
    maintenance_description,
    required_trades,
    candidates,
    target_location=None,
):
    """
    Rank external provider candidates.

    Existing function name and arguments are preserved so
    current callers continue to work.

    This function does not send messages, contact providers,
    or make the final selection.
    """
    if (
        not isinstance(maintenance_description, str)
        or not maintenance_description.strip()
    ):
        raise ValueError(
            "Maintenance description is required"
        )

    if not isinstance(required_trades, list):
        raise ValueError(
            "required_trades must be a list"
        )

    candidates = list(candidates or [])

    if not candidates:
        return []

    scored_candidates = []

    for candidate in candidates:
        if not isinstance(candidate, ExternalWorkerCandidate):
            continue

        score = calculate_external_worker_score(
            candidate=candidate,
            required_trades=required_trades,
            target_location=target_location,
        )

        reason = build_match_reason(
            candidate=candidate,
            score=score,
            required_trades=required_trades,
            target_location=target_location,
        )

        candidate.match_score = score
        candidate.match_reason = reason

        now = datetime.now(timezone.utc)

        candidate.ranking_updated_at = now
        candidate.updated_at = now

        scored_candidates.append(candidate)

    def ranking_key(candidate):
        return (
            getattr(candidate, "match_score", 0) or 0,
            _service_score(candidate, required_trades),
            _location_score(candidate, target_location),
            _availability_score(candidate),
            _rating_score(candidate),
            _review_score(candidate),
        )

    scored_candidates.sort(
        key=ranking_key,
        reverse=True,
    )

    return scored_candidates
