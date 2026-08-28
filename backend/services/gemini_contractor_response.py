
import json
import os
import re

from google import genai


# ============================================================
# GEMINI CLIENT
# ============================================================

_client = None


def get_gemini_client():
    global _client

    if _client is None:

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured"
            )

        _client = genai.Client(
            api_key=api_key
        )

    return _client


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(text):
    """
    Safely extract a JSON object from Gemini's response.
    """

    if not text:
        raise ValueError(
            "Gemini returned an empty response"
        )

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        # Gemini may occasionally return additional text
        # around the JSON object

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                "Gemini did not return valid JSON"
            )

        try:

            return json.loads(
                text[start:end + 1]
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "Gemini returned malformed JSON"
            ) from exc


# ============================================================
# NORMALISATION HELPERS
# ============================================================

def _normalise_price(value):
    """
    Convert Gemini's price into float or None.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value:
        return None

    # Remove common currency symbols and separators
    cleaned = re.sub(
        r"[£$€,\s]",
        "",
        value
    )

    # Handle a price range such as:
    # £150-£200
    # 150 - 200
    if "-" in cleaned:

        parts = cleaned.split("-")

        try:
            return float(parts[0])

        except (ValueError, TypeError):
            return None

    try:

        return float(cleaned)

    except (ValueError, TypeError):
        return None


def _normalise_boolean(value):
    """
    Convert common Gemini boolean responses into:
        True
        False
        None
    """

    if value is True:
        return True

    if value is False:
        return False

    if value is None:
        return None

    if not isinstance(value, str):
        return None

    value = value.strip().lower()

    if value in {
        "true",
        "yes",
        "available",
        "can",
        "can take job",
        "accept",
        "accepted",
        "able"
    }:
        return True

    if value in {
        "false",
        "no",
        "unavailable",
        "cannot",
        "can't",
        "cannot take job",
        "unable",
        "decline",
        "declined"
    }:
        return False

    return None


def _normalise_quality(value):
    """
    Keep response quality within the application's
    supported values.
    """

    if value is None:
        return "unclear"

    value = str(
        value
    ).strip().lower()

    allowed = {
        "good",
        "poor",
        "unavailable",
        "unclear"
    }

    if value in allowed:
        return value

    if value in {
        "positive",
        "good response",
        "clear",
        "clear response"
    }:
        return "good"

    if value in {
        "bad",
        "poor response",
        "negative",
        "vague"
    }:
        return "poor"

    if value in {
        "not available",
        "not_available",
        "cannot take job",
        "unable to take job"
    }:
        return "unavailable"

    return "unclear"


def _normalise_summary(value):
    """
    Ensure Gemini's summary is always a usable string.
    """

    if not isinstance(
        value,
        str
    ):
        return (
            "Contractor response received but "
            "no clear summary was provided."
        )

    value = value.strip()

    if not value:
        return (
            "Contractor response received but "
            "no clear summary was provided."
        )

    return value


def _normalise_estimated_start(value):
    """
    Keep estimated start as a string or None.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    value = str(
        value
    ).strip()

    return value or None


# ============================================================
# MAIN GEMINI ANALYSIS
# ============================================================

def analyse_contractor_response(
    contractor_name,
    contractor_email,
    maintenance_description,
    contractor_response
):
    """
    Analyse a contractor's response using Gemini.

    Returns:

    {
        "response_quality": "good",
        "summary": "...",
        "quoted_price": 150.0,
        "estimated_start": "...",
        "can_take_job": True
    }
    """

    # ========================================================
    # VALIDATION
    # ========================================================

    if not isinstance(
        contractor_response,
        str
    ) or not contractor_response.strip():

        raise ValueError(
            "Contractor response is required"
        )

    if not isinstance(
        maintenance_description,
        str
    ) or not maintenance_description.strip():

        raise ValueError(
            "Maintenance description is required"
        )

    contractor_response = (
        contractor_response.strip()
    )

    maintenance_description = (
        maintenance_description.strip()
    )

    # ========================================================
    # GEMINI PROMPT
    # ========================================================

    prompt = f"""
You are an AI operations assistant for a property
management platform.

You are analysing a contractor's response to a
property maintenance request.

Your task is to extract ONLY information that is
actually present in the contractor's response.

Do not invent information.
Do not infer commitments that the contractor did not make.

============================================================
MAINTENANCE REQUEST
============================================================

{maintenance_description}

============================================================
CONTRACTOR
============================================================

Name:
{contractor_name or "Unknown"}

Email:
{contractor_email or "Unknown"}

============================================================
CONTRACTOR RESPONSE
============================================================

{contractor_response}

============================================================
FIELDS TO EXTRACT
============================================================

1. response_quality

Return exactly one of:

"good"
"poor"
"unavailable"
"unclear"

Use "good" when the response is clear and useful.

Use "poor" when the response is vague, incomplete,
or difficult for a property manager to act upon.

Use "unavailable" when the contractor clearly states
that they cannot take the job.

Use "unclear" when the meaning or availability cannot
reasonably be determined.

------------------------------------------------------------

2. summary

Write a short operational summary for a property manager.

Include relevant information such as:

- whether the contractor can take the job
- quoted price
- proposed start date/time
- questions
- conditions
- limitations
- other important information

Only include information actually present in the response.

------------------------------------------------------------

3. quoted_price

Extract the contractor's quoted price.

Return:

number

if a clear price is provided.

Return:

null

if no price is provided.

If the contractor gives a range, use the lower number.

Do not invent a price.

------------------------------------------------------------

4. estimated_start

Extract the contractor's proposed start time/date.

Examples:

"tomorrow"
"Monday morning"
"next week"
"2026-09-02"

Return null if no start time/date is given.

Do not invent a date.

------------------------------------------------------------

5. can_take_job

Return:

true

if the contractor clearly says they can take the job.

Return:

false

if the contractor clearly says they cannot take the job.

Return:

null

if availability is unclear.

============================================================
IMPORTANT RULES
============================================================

- Use ONLY the contractor response.
- Do not invent facts.
- Do not assume availability.
- Do not assume a price.
- Do not assume a start date.
- Do not turn a question into a commitment.
- Do not turn uncertainty into availability.
- Return JSON only.
- Do not use markdown.
- Do not include explanations outside the JSON.

Return exactly this structure:

{{
    "response_quality": "good",
    "summary": "Short operational summary",
    "quoted_price": 150.00,
    "estimated_start": "Monday morning",
    "can_take_job": true
}}
"""

    # ========================================================
    # CALL GEMINI
    # ========================================================

    client = get_gemini_client()

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0,
                "response_mime_type": "application/json"
            }
        )

    except Exception as exc:

        raise RuntimeError(
            f"Gemini contractor analysis failed: {exc}"
        ) from exc

    # ========================================================
    # GET RESPONSE TEXT
    # ========================================================

    response_text = getattr(
        response,
        "text",
        None
    )

    if not response_text:
        raise RuntimeError(
            "Gemini returned no contractor analysis"
        )

    # ========================================================
    # PARSE JSON
    # ========================================================

    try:

        result = _extract_json(
            response_text
        )

    except ValueError as exc:

        raise RuntimeError(
            "Could not parse Gemini contractor "
            f"analysis: {exc}"
        ) from exc

    if not isinstance(
        result,
        dict
    ):

        raise RuntimeError(
            "Gemini contractor analysis must "
            "be a JSON object"
        )

    # ========================================================
    # NORMALISE RESULT
    # ========================================================

    response_quality = _normalise_quality(
        result.get(
            "response_quality"
        )
    )

    summary = _normalise_summary(
        result.get(
            "summary"
        )
    )

    quoted_price = _normalise_price(
        result.get(
            "quoted_price"
        )
    )

    estimated_start = _normalise_estimated_start(
        result.get(
            "estimated_start"
        )
    )

    can_take_job = _normalise_boolean(
        result.get(
            "can_take_job"
        )
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {
        "response_quality": response_quality,
        "summary": summary,
        "quoted_price": quoted_price,
        "estimated_start": estimated_start,
        "can_take_job": can_take_job
    }

