
import json
import os
import re
import socket
from html import unescape
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from google import genai

from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)


EMAIL_PATTERN = re.compile(
    r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}",
    re.IGNORECASE
)

MAX_PAGE_BYTES = 2_000_000
REQUEST_TIMEOUT = 30

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; PropertyOS Contractor Research/1.0)"
)


def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured"
        )

    return genai.Client(
        api_key=api_key
    )


def _clean_json_response(text):
    if not text:
        return ""

    text = text.strip()

    if text.startswith("```"):
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

    return text.strip()


def _normalise_trade(trade):
    if not isinstance(trade, str):
        return ""

    return trade.strip().lower()


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

        trade = _normalise_trade(
            trade
        )

        if (
            trade
            and trade not in trade_names
        ):
            trade_names.append(
                trade
            )

    return trade_names


def _safe_string(value):
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    return value if value else None


def _safe_float(value):
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if value < 0 or value > 5:
        return None

    return value


def _safe_int(value):
    if value is None:
        return None

    try:
        value = int(value)
    except (TypeError, ValueError):
        return None

    if value < 0:
        return None

    return value


def _normalise_email(value):
    value = _safe_string(
        value
    )

    if not value:
        return None

    value = unescape(
        value
    ).strip()

    value = value.replace(
        "mailto:",
        "",
        1
    )

    value = value.strip(
        " <>\"'()[]{}"
    )

    match = EMAIL_PATTERN.search(
        value
    )

    if not match:
        return None

    email = match.group(0).lower()

    if (
        ".." in email
        or email.startswith(".")
        or email.endswith(".")
    ):
        return None

    return email


def _normalise_phone(value):
    """
    Clean an existing phone number.

    This function NEVER creates or guesses a number.
    """

    value = _safe_string(
        value
    )

    if not value:
        return None

    value = unescape(
        value
    ).strip()

    value = re.sub(
        r"^(tel:|phone:|telephone:)\s*",
        "",
        value,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(
        r"[^\d+().\-\s]",
        "",
        value
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned
    ).strip()

    digit_count = len(
        re.sub(
            r"\D",
            "",
            cleaned
        )
    )

    if digit_count < 7:
        return None

    return cleaned


def _is_public_hostname(hostname):
    """
    Prevent website fetching from resolving to local/private
    network addresses.
    """

    if not hostname:
        return False

    hostname = hostname.lower().strip()

    if hostname in {
        "localhost",
        "localhost.localdomain",
    }:
        return False

    try:
        addresses = socket.getaddrinfo(
            hostname,
            None
        )
    except socket.gaierror:
        return False

    for address in addresses:

        ip = address[4][0]

        try:

            socket.inet_pton(
                socket.AF_INET,
                ip
            )

            first_octet = int(
                ip.split(".")[0]
            )

            second_octet = int(
                ip.split(".")[1]
            )

            if (
                first_octet == 10
                or (
                    first_octet == 172
                    and 16 <= second_octet <= 31
                )
                or (
                    first_octet == 192
                    and second_octet == 168
                )
                or first_octet == 127
            ):
                return False

        except OSError:

            try:

                ip_obj = socket.inet_pton(
                    socket.AF_INET6,
                    ip
                )

                if (
                    ip_obj == b"\x00" * 15 + b"\x01"
                    or ip.lower().startswith("fe80:")
                    or ip.lower().startswith("fc")
                    or ip.lower().startswith("fd")
                ):
                    return False

            except OSError:
                continue

    return True


def _normalise_url(url):
    """
    Validate a URL.

    IMPORTANT:
    This function does NOT guess or construct URLs.
    """

    url = _safe_string(
        url
    )

    if not url:
        return None

    if not url.startswith(
        ("http://", "https://")
    ):
        url = "https://" + url

    parsed = urlparse(
        url
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        return None

    if not parsed.hostname:
        return None

    if not _is_public_hostname(
        parsed.hostname
    ):
        return None

    return url


def _is_valid_business_website(url):
    """
    Accept ONLY URLs that look like an actual business website.

    Rejects:
    - images
    - uploaded assets
    - PDFs
    - documents
    - favicons
    - obvious static files

    We never replace a rejected URL with a guessed URL.
    """

    url = _normalise_url(
        url
    )

    if not url:
        return None

    parsed = urlparse(
        url
    )

    path = parsed.path.lower()

    rejected_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".svg",
        ".ico",
        ".bmp",
        ".avif",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".zip",
        ".mp4",
        ".mp3",
        ".wav",
    )

    if path.endswith(
        rejected_extensions
    ):
        print(
            "[external search] rejected non-website URL: "
            f"{url!r}",
            flush=True
        )

        return None

    rejected_path_fragments = (
        "/wp-content/uploads/",
        "/wp-content/themes/",
        "/wp-content/plugins/",
        "/assets/",
        "/static/",
        "/images/",
        "/image/",
        "/img/",
        "/uploads/",
        "/media/",
    )

    if any(
        fragment in path
        for fragment in rejected_path_fragments
    ):
        print(
            "[external search] rejected asset URL: "
            f"{url!r}",
            flush=True
        )

        return None

    return url


def _fetch_web_page(url):
    """
    Fetch ONLY the exact verified website URL.

    No contact paths are generated.
    """

    url = _is_valid_business_website(
        url
    )

    if not url:
        return None

    try:

        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml"
                ),
            }
        )

        with urlopen(
            request,
            timeout=REQUEST_TIMEOUT
        ) as response:

            content_type = (
                response.headers.get(
                    "Content-Type",
                    ""
                ).lower()
            )

            if (
                "text/html" not in content_type
                and "application/xhtml" not in content_type
            ):
                return None

            data = response.read(
                MAX_PAGE_BYTES
            )

            charset = (
                response.headers.get_content_charset()
                or "utf-8"
            )

            return data.decode(
                charset,
                errors="ignore"
            )

    except Exception as exc:

        print(
            "[external search] website fetch failed: "
            f"url={url!r}, error={exc!r}",
            flush=True
        )

        return None


def _extract_emails_from_html(html):
    """
    Extract publicly visible emails from the exact
    website page.

    No URLs are guessed.
    """

    if not html:
        return []

    html = unescape(
        html
    )

    found = []

    for match in EMAIL_PATTERN.findall(
        html
    ):

        email = _normalise_email(
            match
        )

        if (
            email
            and email not in found
        ):
            found.append(
                email
            )

    mailto_pattern = re.compile(
        r"mailto:\s*([^\"'\s?<>]+)",
        re.IGNORECASE
    )

    for match in mailto_pattern.findall(
        html
    ):

        email = _normalise_email(
            match
        )

        if (
            email
            and email not in found
        ):
            found.append(
                email
            )

    text = re.sub(
        r"<[^>]+>",
        " ",
        html
    )

    text = unescape(
        text
    )

    obfuscated_patterns = [

        re.compile(
            r"\b([A-Z0-9._%+\-]+)\s*"
            r"(?:\[at\]|\(at\)|\{at\}|\bat\b)\s*"
            r"([A-Z0-9.\-]+\.[A-Z]{2,})\b",
            re.IGNORECASE
        ),

        re.compile(
            r"\b([A-Z0-9._%+\-]+)\s*"
            r"(?:\[at\]|\(at\)|\{at\})\s*"
            r"([A-Z0-9.\-]+\.[A-Z]{2,})\b",
            re.IGNORECASE
        ),
    ]

    for pattern in obfuscated_patterns:

        for match in pattern.findall(
            text
        ):

            email = (
                f"{match[0]}@{match[1]}"
            )

            email = _normalise_email(
                email
            )

            if (
                email
                and email not in found
            ):
                found.append(
                    email
                )

    return found


def _extract_phones_from_html(html):
    """
    Extract phone numbers that actually appear on the
    exact website page.

    This NEVER generates or guesses a number.
    """

    if not html:
        return []

    text = re.sub(
        r"<[^>]+>",
        " ",
        html
    )

    text = unescape(
        text
    )

    patterns = [

        re.compile(
            r"(?:\+44\s?\(?0?\)?|0)"
            r"(?:\s?\(?\d{2,4}\)?){2,4}"
            r"(?:\s?\d{2,4})?"
        ),

        re.compile(
            r"\+\d{1,3}"
            r"(?:[\s().-]?\d){7,14}"
        ),
    ]

    found = []

    for pattern in patterns:

        for match in pattern.findall(
            text
        ):

            phone = _normalise_phone(
                match
            )

            if (
                phone
                and phone not in found
            ):
                found.append(
                    phone
                )

    return found


def _verify_website_details(
    provider,
    website
):
    """
    Check the exact website Gemini returned.

    We do NOT try:
    /contact
    /contact-us
    /about
    /enquiries
    etc.
    """

    result = {
        "email": None,
        "phone": None,
    }

    website = _is_valid_business_website(
        website
    )

    if not website:
        return result

    print(
        "[external search] verifying exact website: "
        f"{website!r}",
        flush=True
    )

    html = _fetch_web_page(
        website
    )

    if not html:
        return result

    emails = _extract_emails_from_html(
        html
    )

    phones = _extract_phones_from_html(
        html
    )

    if emails:

        result["email"] = emails[0]

        print(
            "[external search] verified website email: "
            f"name={provider.get('name')!r}, "
            f"email={emails[0]!r}",
            flush=True
        )

    if phones:

        result["phone"] = phones[0]

        print(
            "[external search] verified website phone: "
            f"name={provider.get('name')!r}, "
            f"phone={phones[0]!r}",
            flush=True
        )

    return result


def search_external_workers(
    maintenance_request_id,
    required_trades,
    location=None
):
    """
    Discover real external contractors using Gemini
    with Google Search grounding.

    Gemini provides the candidate information.

    The backend:
    - validates the returned website
    - rejects image/static asset URLs
    - verifies the exact returned website
    - extracts public phone/email when present
    - never invents missing information
    - never constructs contact URLs
    """

    if not maintenance_request_id:
        raise ValueError(
            "maintenance_request_id is required"
        )

    trade_names = _extract_trade_names(
        required_trades
    )

    if not trade_names:
        return []

    location_text = _safe_string(
        location
    )

    if not location_text:
        location_text = (
            "the relevant local area"
        )

    client = _get_gemini_client()

    trades_text = ", ".join(
        trade_names
    )

    prompt = f"""
Find real businesses that provide these property
maintenance services:

Trades: {trades_text}
Location: {location_text}

Use Google Search grounding and current public web
information.

Return ONLY JSON in this format:

{{
  "providers": [
    {{
      "name": "Business name",
      "trade": "trade",
      "location": "verified location or null",
      "rating": 4.8,
      "review_count": 100,
      "availability": null,
      "website": "https://business-homepage.co.uk",
      "phone": "01234567890",
      "email": "info@business.co.uk",
      "source_url": "https://real-source-page.co.uk"
    }}
  ]
}}

Rules:

1. Only return real businesses supported by search
   evidence.

2. Never invent a business.

3. Never guess any field.

4. If a field cannot be verified, return null.

5. The website must be the actual business homepage.

6. The website must NOT be an image.

7. The website must NOT be a file or uploaded asset.

8. Never return URLs ending in .jpg .jpeg .png .webp
   .gif .svg .pdf or similar file extensions.

9. Never return URLs containing /wp-content/uploads/.

10. Do not construct a website from the business name.

11. Do not construct contact URLs.

12. The phone number must be an actual publicly listed
    business phone number.

13. The email must be an actual publicly listed
    business email.

14. The rating and review count must be supported by
    search evidence.

15. The location must be supported by search evidence.

16. source_url must be an actual URL from the search
    evidence.

17. Prefer the official business website when available.

18. Only return businesses relevant to the requested
    trades.

19. Prefer businesses near the target location.

20. Return up to 10 strong candidates.

21. A business must appear only once.

22. Accuracy is more important than completeness.

23. Missing information must be null.

24. Do not output explanations.

25. Do not output markdown.
"""

    try:

        response = client.interactions.create(
            model=os.getenv(
                "GEMINI_MODEL",
                "gemini-3.6-flash"
            ),
            input=prompt,
            tools=[
                {
                    "type": "google_search"
                }
            ],
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": {
                    "type": "object",
                    "properties": {
                        "providers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {

                                    "name": {
                                        "type": "string"
                                    },

                                    "trade": {
                                        "type": "string"
                                    },

                                    "location": {
                                        "type": [
                                            "string",
                                            "null"
                                        ]
                                    },

                                    "rating": {
                                        "type": [
                                            "number",
                                            "null"
                                        ]
                                    },

                                    "review_count": {
                                        "type": [
                                            "integer",
                                            "null"
                                        ]
                                    },

                                    "availability": {
                                        "type": [
                                            "string",
                                            "null"
                                        ]
                                    },

                                    "website": {
                                        "type": [
                                            "string",
                                            "null"
                                        ]
                                    },

                                    "phone": {
                                        "type": [
                                            "string",
                                            "null"
                                        ]
                                    },

                                    "email": {
                                        "type": [
                                            "string",
                                            "null"
                                        ]
                                    },

                                    "source_url": {
                                        "type": [
                                            "string",
                                            "null"
                                        ]
                                    }
                                },

                                "required": [
                                    "name",
                                    "trade"
                                ]
                            }
                        }
                    },

                    "required": [
                        "providers"
                    ]
                }
            },

            generation_config={
                "thinking_level": "low",
                "max_output_tokens": 8192
            }
        )

    except Exception as exc:

        print(
            "[external search] Gemini discovery error: "
            f"{exc!r}",
            flush=True
        )

        raise RuntimeError(
            f"Gemini provider search failed: {exc}"
        ) from exc

    try:

        response_debug = response.model_dump(
            exclude_none=True
        )

    except AttributeError:

        response_debug = repr(
            response
        )

    print(
        "[external search] Gemini structured response: "
        f"{response_debug!r}",
        flush=True
    )

    output = getattr(
        response,
        "output_text",
        None
    )

    output = _clean_json_response(
        output
    )

    print(
        "[external search] Gemini raw response: "
        f"{output!r}",
        flush=True
    )

    if not output:

        print(
            "[external search] Gemini returned an empty response",
            flush=True
        )

        return []

    try:

        data = json.loads(
            output
        )

    except json.JSONDecodeError as exc:

        print(
            "[external search] Gemini response was not valid JSON: "
            f"{exc!r}",
            flush=True
        )

        raise RuntimeError(
            "Gemini returned invalid provider JSON"
        ) from exc

    if not isinstance(
        data,
        dict
    ):
        return []

    providers = data.get(
        "providers",
        []
    )

    if not isinstance(
        providers,
        list
    ):
        return []

    print(
        "[external search] Gemini providers before validation: "
        f"{len(providers)}",
        flush=True
    )

    candidates = []

    seen_businesses = set()

    for provider in providers:

        if not isinstance(
            provider,
            dict
        ):
            continue

        name = _safe_string(
            provider.get("name")
        )

        if not name:
            continue

        trade = _normalise_trade(
            provider.get("trade")
        )

        if not trade:
            continue

        if trade not in trade_names:

            print(
                "[external search] rejected provider: "
                f"trade mismatch name={name!r}, "
                f"trade={trade!r}",
                flush=True
            )

            continue

        business_key = (
            name.lower(),
            trade
        )

        if business_key in seen_businesses:

            print(
                "[external search] rejected duplicate: "
                f"{name!r}",
                flush=True
            )

            continue

        seen_businesses.add(
            business_key
        )

        location_value = _safe_string(
            provider.get("location")
        )

        rating = _safe_float(
            provider.get("rating")
        )

        review_count = _safe_int(
            provider.get("review_count")
        )

        availability = _safe_string(
            provider.get("availability")
        )

        # -------------------------------------------------
        # WEBSITE
        #
        # This rejects image URLs and static assets.
        # It never guesses a replacement.
        # -------------------------------------------------

        website = _is_valid_business_website(
            provider.get("website")
        )

        # -------------------------------------------------
        # CONTACT DETAILS
        #
        # Start with Gemini's values only.
        # Nothing is generated.
        # -------------------------------------------------

        phone = _normalise_phone(
            provider.get("phone")
        )

        email = _normalise_email(
            provider.get("email")
        )

        # -------------------------------------------------
        # VERIFY EXACT WEBSITE
        #
        # No /contact
        # No /about
        # No guessed paths.
        # -------------------------------------------------

        if website:

            verified = _verify_website_details(
                provider=provider,
                website=website
            )

            if verified.get("phone"):
                phone = verified[
                    "phone"
                ]

            if verified.get("email"):
                email = verified[
                    "email"
                ]

        source_url = _normalise_url(
            provider.get(
                "source_url"
            )
        )

        external_id = (
            f"gemini-web-"
            f"{maintenance_request_id}-"
            f"{len(candidates) + 1}"
        )

        candidate = ExternalWorkerCandidate(
            maintenance_request_id=(
                maintenance_request_id
            ),

            provider="gemini_web_search",

            external_id=external_id,

            name=name,

            trade=trade,

            location=location_value,

            rating=rating,

            review_count=review_count,

            availability=availability,

            website=website,

            phone=phone,

            email=email,

            source_url=source_url,

          
        )

        candidates.append(
            candidate
        )

        print(
            "[external search] candidate: "
            f"name={name!r}, "
            f"trade={trade!r}, "
            f"website={website!r}, "
            f"phone={phone!r}, "
            f"email={email!r}, "
            f"source={source_url!r}",
            flush=True
        )

    print(
        "[external search] valid candidates created: "
        f"{len(candidates)}",
        flush=True
    )

    return candidates


def find_contractors_with_gemini(
    maintenance_request_id,
    required_trades,
    location=None
):
    return search_external_workers(
        maintenance_request_id=(
            maintenance_request_id
        ),
        required_trades=required_trades,
        location=location
    )