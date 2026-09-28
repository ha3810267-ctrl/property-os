
import json
import os
import re
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# Website requests now run concurrently, so a slow website
# does not block all of the other contractor checks.
REQUEST_TIMEOUT = 10

# Maximum number of websites checked simultaneously.
MAX_PARALLEL_WEBSITE_CHECKS = 8

TARGET_CONTRACTORS = 20

# Gemini gets one retry when it returns malformed JSON.
MAX_GEMINI_JSON_ATTEMPTS = 2

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; PropertyOS Contractor Research/1.0)"
)


# ============================================================
# GEMINI
# ============================================================

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


def _extract_json_object(text):
    """
    Extract the outermost JSON object if Gemini wrapped
    the JSON in additional text.

    This does NOT attempt to repair malformed JSON.
    It only removes surrounding non-JSON content.
    """

    if not text:
        return ""

    text = text.strip()

    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return text

    return text[start:end + 1].strip()


def _parse_provider_json(output):
    """
    Parse Gemini provider JSON safely.

    First try the complete cleaned response.
    Then try extracting the outer JSON object.
    """

    output = _clean_json_response(
        output
    )

    if not output:
        return None

    try:
        return json.loads(
            output
        )

    except json.JSONDecodeError:
        pass

    extracted = _extract_json_object(
        output
    )

    if extracted != output:

        try:
            return json.loads(
                extracted
            )

        except json.JSONDecodeError:
            pass

    return None


# ============================================================
# NORMALISATION
# ============================================================

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


# ============================================================
# EMAIL
# ============================================================

PLACEHOLDER_EMAIL_DOMAINS = {
    "domain.com",
    "example.com",
    "example.org",
    "example.net",
}

PLACEHOLDER_EMAIL_LOCAL_PARTS = {
    "user",
    "test",
    "example",
    "name",
    "email",
}


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


def _is_valid_public_email(email):
    """
    Validate an email as a usable public business email.

    This deliberately rejects obvious placeholder addresses
    while allowing legitimate free-email providers such as
    Gmail, Yahoo and Hotmail.
    """

    email = _normalise_email(
        email
    )

    if not email:
        return False

    local_part, separator, domain = (
        email.rpartition("@")
    )

    if (
        not separator
        or not local_part
        or not domain
    ):
        return False

    if domain in PLACEHOLDER_EMAIL_DOMAINS:
        return False

    if local_part in PLACEHOLDER_EMAIL_LOCAL_PARTS:
        return False

    return True


# ============================================================
# PHONE
# ============================================================

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


# ============================================================
# WEBSITE VALIDATION
# ============================================================

def _is_public_hostname(hostname):
    """
    Prevent website fetching from resolving to local/private
    network addresses.

    This function is deliberately defensive because Gemini
    search results can occasionally contain malformed website
    strings.
    """

    if not hostname:
        return False

    try:
        hostname = hostname.strip().lower()
    except Exception:
        return False

    if not hostname:
        return False

    if len(hostname) > 253:
        return False

    if any(
        character.isspace()
        for character in hostname
    ):
        return False

    if hostname.startswith(".") or hostname.endswith("."):
        return False

    labels = hostname.rstrip(".").split(".")

    if not labels:
        return False

    for label in labels:

        if not label:
            return False

        if len(label) > 63:
            return False

        if label.startswith("-") or label.endswith("-"):
            return False

        try:
            ascii_label = label.encode(
                "idna"
            ).decode(
                "ascii"
            )
        except (
            UnicodeError,
            UnicodeEncodeError,
            UnicodeDecodeError,
            ValueError
        ):
            return False

        if len(ascii_label) > 63:
            return False

        if not re.fullmatch(
            r"[A-Za-z0-9-]+",
            ascii_label
        ):
            return False

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
    except (
        socket.gaierror,
        UnicodeError,
        ValueError,
        OSError
    ):
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

                socket.inet_pton(
                    socket.AF_INET6,
                    ip
                )

                if (
                    ip.lower() == "::1"
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

    if any(
        character.isspace()
        for character in url
    ):
        print(
            "[external search] rejected malformed website "
            f"containing whitespace: {url!r}",
            flush=True
        )

        return None

    if len(url) > 2048:
        print(
            "[external search] rejected oversized website "
            f"value: length={len(url)}",
            flush=True
        )

        return None

    if not url.startswith(
        ("http://", "https://")
    ):
        url = "https://" + url

    try:
        parsed = urlparse(
            url
        )
    except (
        ValueError,
        UnicodeError
    ) as exc:

        print(
            "[external search] rejected malformed website URL: "
            f"url={url!r}, error={exc!r}",
            flush=True
        )

        return None

    if parsed.scheme not in {
        "http",
        "https",
    }:
        return None

    try:
        hostname = parsed.hostname
    except (
        ValueError,
        UnicodeError
    ) as exc:

        print(
            "[external search] rejected invalid hostname: "
            f"url={url!r}, error={exc!r}",
            flush=True
        )

        return None

    if not hostname:
        return None

    if not _is_public_hostname(
        hostname
    ):
        print(
            "[external search] rejected invalid/private "
            f"website hostname: {hostname!r}",
            flush=True
        )

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
    """

    url = _normalise_url(
        url
    )

    if not url:
        return None

    try:
        parsed = urlparse(
            url
        )
    except (
        ValueError,
        UnicodeError
    ):
        return None

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


# ============================================================
# WEBSITE FETCHING
# ============================================================

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


def _verify_provider_website(provider):
    """
    Verify one provider website.

    This helper is intentionally isolated so multiple
    contractor websites can be checked concurrently.
    """

    website = _is_valid_business_website(
        provider.get("website")
    )

    if not website:
        return {
            "website": None,
            "email": None,
            "phone": None,
        }

    try:

        verified = _verify_website_details(
            provider=provider,
            website=website
        )

    except Exception as exc:

        print(
            "[external search] parallel website verification "
            f"failed: name={provider.get('name')!r}, "
            f"website={website!r}, error={exc!r}",
            flush=True
        )

        return {
            "website": website,
            "email": None,
            "phone": None,
        }

    return {
        "website": website,
        "email": verified.get("email"),
        "phone": verified.get("phone"),
    }


def _verify_provider_websites_parallel(providers):
    """
    Verify all usable provider websites concurrently.

    Results are returned in the SAME ORDER as providers,
    so the rest of the discovery pipeline remains deterministic.
    """

    results = [
        {
            "website": None,
            "email": None,
            "phone": None,
        }
        for _ in providers
    ]

    website_indexes = []

    for index, provider in enumerate(providers):

        if not isinstance(
            provider,
            dict
        ):
            continue

        website = _is_valid_business_website(
            provider.get("website")
        )

        if website:
            website_indexes.append(
                index
            )

    if not website_indexes:
        return results

    print(
        "[external search] starting parallel website "
        f"verification: "
        f"{len(website_indexes)} websites, "
        f"max_workers={MAX_PARALLEL_WEBSITE_CHECKS}",
        flush=True
    )

    with ThreadPoolExecutor(
        max_workers=MAX_PARALLEL_WEBSITE_CHECKS
    ) as executor:

        futures = {
            executor.submit(
                _verify_provider_website,
                providers[index]
            ): index
            for index in website_indexes
        }

        for future in as_completed(
            futures
        ):

            index = futures[
                future
            ]

            try:

                results[index] = (
                    future.result()
                )

            except Exception as exc:

                provider = providers[index]

                print(
                    "[external search] unexpected parallel "
                    "verification error: "
                    f"name={provider.get('name')!r}, "
                    f"error={exc!r}",
                    flush=True
                )

                results[index] = {
                    "website": _is_valid_business_website(
                        provider.get("website")
                    ),
                    "email": None,
                    "phone": None,
                }

    print(
        "[external search] parallel website verification "
        "complete",
        flush=True
    )

    return results


# ============================================================
# LOCATION SEARCH
# ============================================================

def _location_search_tiers(location):
    """
    Return progressively wider geographic search instructions.

    We deliberately search locally first and only broaden the
    area when we still need more qualifying contractors.
    """

    location = _safe_string(
        location
    )

    if not location:
        location = "the property's local area"

    return [
        (
            "local",
            f"""
Search primarily within the exact target area:

{location}

Prioritise businesses physically located in this area
or clearly serving this exact area.
Do not broaden the search unnecessarily.
"""
        ),
        (
            "nearby",
            f"""
Search around the target location:

{location}

Prioritise nearby towns, suburbs, districts and surrounding
areas immediately adjacent to the target location.

Businesses farther away should only be considered when
there are not enough suitable businesses in the target area.
"""
        ),
        (
            "surrounding",
            f"""
Search the wider surrounding area around:

{location}

Prioritise contractors that explicitly state they serve the
target location and nearby communities.

Do not favour a distant business merely because it has
more reviews.
"""
        ),
        (
            "wider",
            f"""
Search a wider reasonable service area around:

{location}

The goal is to find additional legitimate contractors
that publicly state they serve the target location.

Still prioritise businesses that are geographically close
to the property.
"""
        ),
    ]


# ============================================================
# GEMINI DISCOVERY
# ============================================================

def _build_discovery_prompt(
    trades_text,
    location_instruction,
    excluded_businesses,
    batch_number,
    retry=False
):
    excluded_text = ""

    if excluded_businesses:

        excluded_names = list(
            excluded_businesses
        )[:100]

        excluded_text = (
            "\n\nBusinesses already found. "
            "Do NOT return these again:\n"
            + "\n".join(
                f"- {name}"
                for name in excluded_names
            )
        )

    retry_instruction = ""

    if retry:
        retry_instruction = """
IMPORTANT:
The previous response could not be parsed as valid JSON.
Return the response again as COMPLETE valid JSON.
Do not truncate any strings.
Do not include markdown fences.
Do not include explanations before or after the JSON.
"""

    return f"""
Find real businesses that provide these property
maintenance services:

Trades: {trades_text}

{location_instruction}

Use Google Search grounding and current public web
information.

This is search batch {batch_number}.

We ultimately need 20 qualifying contractors with
publicly verifiable business email addresses.

Return a LARGE pool of strong candidates in this batch,
preferably around 15-20 businesses.

{excluded_text}

{retry_instruction}

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

14. The location must be supported by search evidence.

15. The rating and review count must be supported by
    search evidence.

16. source_url must be an actual URL from the search
    evidence.

17. Prefer the official business website when available.

18. Only return businesses relevant to the requested
    trades.

19. Strongly prioritise geographic proximity to the
    target property.

20. Prefer businesses that explicitly state they serve
    the target area.

21. Do not return businesses already listed above.

22. A business must appear only once.

23. Missing information must be null.

24. Do not output explanations.

25. Do not output markdown.
"""


def _request_gemini_provider_batch(
    client,
    prompt
):
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

    data = _parse_provider_json(
        output
    )

    if data is None:

        raise ValueError(
            "Gemini returned malformed provider JSON"
        )

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

    return providers


def _discover_provider_batch(
    client,
    trades_text,
    location_instruction,
    excluded_businesses,
    batch_number
):
    """
    Ask Gemini for another batch of real businesses.

    If Gemini returns malformed JSON, retry the same search
    once with an explicit instruction to return complete JSON.
    """

    for attempt in range(
        1,
        MAX_GEMINI_JSON_ATTEMPTS + 1
    ):

        retry = attempt > 1

        prompt = _build_discovery_prompt(
            trades_text=trades_text,
            location_instruction=location_instruction,
            excluded_businesses=excluded_businesses,
            batch_number=batch_number,
            retry=retry
        )

        try:

            providers = _request_gemini_provider_batch(
                client=client,
                prompt=prompt
            )

            print(
                "[external search] Gemini JSON parsed "
                f"successfully on attempt {attempt}",
                flush=True
            )

            return providers

        except ValueError as exc:

            print(
                "[external search] Gemini returned invalid "
                f"provider JSON on attempt {attempt}/"
                f"{MAX_GEMINI_JSON_ATTEMPTS}: "
                f"{exc!r}",
                flush=True
            )

            if attempt >= MAX_GEMINI_JSON_ATTEMPTS:

                raise RuntimeError(
                    "Gemini returned invalid provider JSON "
                    "after retry"
                ) from exc

    return []


# ============================================================
# MAIN SEARCH
# ============================================================

def search_external_workers(
    maintenance_request_id,
    required_trades,
    location=None
):
    """
    Discover exactly up to 20 qualifying external contractors.

    Search strategy:

    1. Exact local area
    2. Nearby areas
    3. Wider surrounding area
    4. Wider service area

    Contractors without a publicly verified email are
    excluded.

    The search continues into wider geographic areas until
    20 qualifying contractors have been found or the
    available search results are exhausted.
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
            "the property's local area"
        )

    client = _get_gemini_client()

    trades_text = ", ".join(
        trade_names
    )

    location_tiers = _location_search_tiers(
        location_text
    )

    candidates = []

    seen_businesses = set()
    seen_emails = set()

    for tier_name, location_instruction in location_tiers:

        if len(candidates) >= TARGET_CONTRACTORS:
            break

        print(
            "[external search] starting location tier: "
            f"{tier_name!r}, "
            f"current qualifying candidates="
            f"{len(candidates)}",
            flush=True
        )

        for batch_number in range(1, 3):

            if len(candidates) >= TARGET_CONTRACTORS:
                break

            providers = _discover_provider_batch(
                client=client,
                trades_text=trades_text,
                location_instruction=location_instruction,
                excluded_businesses=seen_businesses,
                batch_number=batch_number
            )

            print(
                "[external search] providers returned: "
                f"tier={tier_name!r}, "
                f"batch={batch_number}, "
                f"count={len(providers)}",
                flush=True
            )

            # -------------------------------------------------
            # PRE-FILTER PROVIDERS
            # -------------------------------------------------

            prepared_providers = []

            for provider in providers:

                if len(candidates) >= TARGET_CONTRACTORS:
                    break

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

                prepared_providers.append(
                    provider
                )

            if not prepared_providers:
                continue

            # -------------------------------------------------
            # PARALLEL WEBSITE VERIFICATION
            # -------------------------------------------------

            verification_results = (
                _verify_provider_websites_parallel(
                    prepared_providers
                )
            )

            # -------------------------------------------------
            # PROCESS VERIFIED RESULTS
            # -------------------------------------------------

            for index, provider in enumerate(
                prepared_providers
            ):

                if len(candidates) >= TARGET_CONTRACTORS:
                    break

                name = _safe_string(
                    provider.get("name")
                )

                trade = _normalise_trade(
                    provider.get("trade")
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

                verification = (
                    verification_results[index]
                    if index < len(
                        verification_results
                    )
                    else {
                        "website": None,
                        "email": None,
                        "phone": None,
                    }
                )

                website = verification.get(
                    "website"
                )

                phone = _normalise_phone(
                    provider.get("phone")
                )

                email = _normalise_email(
                    provider.get("email")
                )

                # Prefer information actually found on the
                # exact verified business website.
                if verification.get("phone"):
                    phone = verification[
                        "phone"
                    ]

                if verification.get("email"):
                    email = verification[
                        "email"
                    ]

                # -------------------------------------------------
                # PUBLIC EMAIL REQUIREMENT
                # -------------------------------------------------

                if not _is_valid_public_email(
                    email
                ):

                    print(
                        "[external search] rejected contractor "
                        "without valid public business email: "
                        f"name={name!r}, "
                        f"email={email!r}",
                        flush=True
                    )

                    continue

                if email in seen_emails:

                    print(
                        "[external search] rejected duplicate "
                        f"email: {email!r}",
                        flush=True
                    )

                    continue

                seen_emails.add(
                    email
                )

                external_id = (
                    f"gemini-web-"
                    f"{maintenance_request_id}-"
                    f"{len(candidates) + 1}"
                )

                source_url = _normalise_url(
                    provider.get(
                        "source_url"
                    )
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
                    "[external search] QUALIFYING "
                    f"contractor {len(candidates)}/"
                    f"{TARGET_CONTRACTORS}: "
                    f"name={name!r}, "
                    f"trade={trade!r}, "
                    f"location={location_value!r}, "
                    f"email={email!r}, "
                    f"tier={tier_name!r}",
                    flush=True
                )

    print(
        "[external search] final qualifying candidates: "
        f"{len(candidates)}/{TARGET_CONTRACTORS}",
        flush=True
    )

    if len(candidates) < TARGET_CONTRACTORS:

        print(
            "[external search] WARNING: fewer than 20 "
            "qualifying contractors were found after "
            "all geographic search tiers.",
            flush=True
        )

    return candidates[:TARGET_CONTRACTORS]


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

