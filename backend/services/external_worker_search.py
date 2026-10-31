
import json
import os
import re
import secrets
import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from google import genai

from backend.models.external_worker_candidate import ExternalWorkerCandidate
from backend.services.email import send_email

sys.set_int_max_str_digits(100000)

EMAIL_PATTERN = re.compile(
    r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}",
    re.IGNORECASE,
)

MAX_PAGE_BYTES = 2_000_000
REQUEST_TIMEOUT = 10
MAX_PARALLEL_WEBSITE_CHECKS = 8

TARGET_CONTRACTORS = 20
MAX_GEMINI_JSON_ATTEMPTS = 5

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; Matchly Provider Research/1.0)"
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

    return genai.Client(api_key=api_key)


def _clean_json_response(text):
    if not text:
        return ""

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"\s*```$", "", text)

    return text.strip()


def _extract_json_object(text):
    """Extract the first complete JSON object without damaging strings."""
    if not text:
        return ""

    text = text.strip().lstrip("\ufeff")
    start = text.find("{")

    if start < 0:
        return ""

    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1

            if depth == 0:
                return text[start:index + 1].strip()

    return ""


def _parse_provider_json(output):
    """
    Parse provider JSON while allowing individual malformed
    candidates to be handled separately by the batch parser.
    """
    output = _clean_json_response(output)

    if not output:
        return None

    try:
        data = json.loads(output)

        if isinstance(data, dict):
            return data

    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    extracted = _extract_json_object(output)

    if not extracted:
        return None

    try:
        data = json.loads(extracted)

        if isinstance(data, dict):
            return data

    except (json.JSONDecodeError, TypeError, ValueError):
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
    """
    Preserve the existing required_trades interface for
    compatibility, but accept any service category.

    Items may be strings or dictionaries containing:
        trade: service/provider type
        reason: why the service is required
    """
    trade_names = []

    for item in required_trades or []:
        if isinstance(item, dict):
            value = item.get("trade", "")
        else:
            value = str(item)

        value = _normalise_trade(value)

        if value and value not in trade_names:
            trade_names.append(value)

    return trade_names


def _format_service_requirements(required_trades):
    requirements = []

    for item in required_trades or []:
        if isinstance(item, dict):
            service = _safe_string(item.get("trade"))
            reason = _safe_string(item.get("reason"))

            if service:
                if reason:
                    requirements.append(
                        f"- {service}: {reason}"
                    )
                else:
                    requirements.append(
                        f"- {service}"
                    )

        else:
            service = _safe_string(item)

            if service:
                requirements.append(f"- {service}")

    return "\n".join(requirements)


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
    except (TypeError, ValueError, OverflowError):
        return None

    if value < 0 or value > 10_000_000:
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
    value = _safe_string(value)

    if not value:
        return None

    value = unescape(value).strip()
    value = value.replace("mailto:", "", 1)
    value = value.strip(" <>\"'()[]{}")

    match = EMAIL_PATTERN.search(value)

    if not match:
        return None

    email = match.group(0).lower()

    if ".." in email or email.startswith(".") or email.endswith("."):
        return None

    return email


def _is_valid_public_email(email):
    email = _normalise_email(email)

    if not email:
        return False

    local_part, separator, domain = email.rpartition("@")

    if not separator or not local_part or not domain:
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
    value = _safe_string(value)

    if not value:
        return None

    value = unescape(value).strip()

    value = re.sub(
        r"^(tel:|phone:|telephone:)\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(r"[^\d+().\-\s]", "", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    digit_count = len(re.sub(r"\D", "", cleaned))

    if digit_count < 7:
        return None

    return cleaned


# ============================================================
# WEBSITE VALIDATION
# ============================================================

def _is_public_hostname(hostname):
    if not hostname:
        return False

    hostname = hostname.strip().lower()

    if not hostname or len(hostname) > 253:
        return False

    if any(character.isspace() for character in hostname):
        return False

    if hostname.startswith(".") or hostname.endswith("."):
        return False

    labels = hostname.rstrip(".").split(".")

    if not labels:
        return False

    for label in labels:
        if not label or len(label) > 63:
            return False

        if label.startswith("-") or label.endswith("-"):
            return False

        try:
            ascii_label = label.encode("idna").decode("ascii")
        except (UnicodeError, ValueError):
            return False

        if len(ascii_label) > 63:
            return False

        if not re.fullmatch(r"[A-Za-z0-9-]+", ascii_label):
            return False

    if hostname in {"localhost", "localhost.localdomain"}:
        return False

    try:
        addresses = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, UnicodeError, ValueError, OSError):
        return False

    for address in addresses:
        ip = address[4][0]

        try:
            socket.inet_pton(socket.AF_INET, ip)

            octets = [int(part) for part in ip.split(".")]

            if (
                octets[0] == 10
                or octets[0] == 127
                or (
                    octets[0] == 172
                    and 16 <= octets[1] <= 31
                )
                or (
                    octets[0] == 192
                    and octets[1] == 168
                )
                or octets[0] == 0
                or octets[0] >= 224
            ):
                return False

            continue

        except (OSError, ValueError):
            pass

        try:
            socket.inet_pton(socket.AF_INET6, ip)

            ip_lower = ip.lower()

            if (
                ip_lower == "::1"
                or ip_lower.startswith("fe80:")
                or ip_lower.startswith("fc")
                or ip_lower.startswith("fd")
                or ip_lower == "::"
            ):
                return False

        except OSError:
            continue

    return True


def _normalise_url(url):
    """Validate a public HTTP(S) URL without inventing its path."""
    url = _safe_string(url)
    if not url:
        return None

    if any(character.isspace() or ord(character) < 32 for character in url):
        return None

    if len(url) > 2048:
        return None

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
    except (ValueError, UnicodeError):
        return None

    if parsed.scheme not in {"http", "https"}:
        return None
    if not hostname or not _is_public_hostname(hostname):
        return None

    path = parsed.path or ""
    if len(path) > 512:
        return None
    if re.search(r"(?:-2){4,}", path, flags=re.IGNORECASE):
        return None
    if re.search(r"(?:/[^/]+){10,}", path):
        return None

    return url


def _is_valid_business_website(url):
    url = _normalise_url(url)

    if not url:
        return None

    try:
        parsed = urlparse(url)
    except (ValueError, UnicodeError):
        return None

    path = parsed.path.lower()

    rejected_extensions = (
        ".jpg", ".jpeg", ".png", ".webp", ".gif",
        ".svg", ".ico", ".bmp", ".avif", ".pdf",
        ".doc", ".docx", ".xls", ".xlsx", ".zip",
        ".mp4", ".mp3", ".wav",
    )

    if path.endswith(rejected_extensions):
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

    if any(fragment in path for fragment in rejected_path_fragments):
        return None

    return url


# ============================================================
# WEBSITE FETCHING
# ============================================================

def _fetch_web_page(url):
    url = _is_valid_business_website(url)

    if not url:
        return None

    try:
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
            },
        )

        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            content_type = response.headers.get(
                "Content-Type", ""
            ).lower()

            if (
                "text/html" not in content_type
                and "application/xhtml" not in content_type
            ):
                return None

            data = response.read(MAX_PAGE_BYTES)

            charset = (
                response.headers.get_content_charset()
                or "utf-8"
            )

            return data.decode(charset, errors="ignore")

    except Exception as exc:
        print(
            "[external search] website fetch failed: "
            f"url={url!r}, error={exc!r}",
            flush=True,
        )
        return None


def _extract_emails_from_html(html):
    if not html:
        return []

    html = unescape(html)
    found = []

    for match in EMAIL_PATTERN.findall(html):
        email = _normalise_email(match)

        if email and email not in found:
            found.append(email)

    mailto_pattern = re.compile(
        r"mailto:\s*([^\"'\s?<>]+)",
        re.IGNORECASE,
    )

    for match in mailto_pattern.findall(html):
        email = _normalise_email(match)

        if email and email not in found:
            found.append(email)

    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)

    obfuscated_pattern = re.compile(
        r"\b([A-Z0-9._%+\-]+)\s*"
        r"(?:\[at\]|\(at\)|\{at\}|\bat\b)\s*"
        r"([A-Z0-9.\-]+\.[A-Z]{2,})\b",
        re.IGNORECASE,
    )

    for match in obfuscated_pattern.findall(text):
        email = _normalise_email(
            f"{match[0]}@{match[1]}"
        )

        if email and email not in found:
            found.append(email)

    return found


def _extract_phones_from_html(html):
    if not html:
        return []

    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)

    patterns = [
        re.compile(
            r"(?:\+44\s?\(?0?\)?|0)"
            r"(?:\s?\(?\d{2,4}\)?){2,4}"
            r"(?:\s?\d{2,4})?"
        ),
        re.compile(
            r"\+\d{1,3}(?:[\s().-]?\d){7,14}"
        ),
    ]

    found = []

    for pattern in patterns:
        for match in pattern.findall(text):
            phone = _normalise_phone(match)

            if phone and phone not in found:
                found.append(phone)

    return found


def _verify_website_details(provider, website):
    result = {"email": None, "phone": None}

    website = _is_valid_business_website(website)

    if not website:
        return result

    html = _fetch_web_page(website)

    if not html:
        return result

    emails = _extract_emails_from_html(html)
    phones = _extract_phones_from_html(html)

    if emails:
        result["email"] = emails[0]

    if phones:
        result["phone"] = phones[0]

    return result


def _discover_provider_websites(client, providers):
    """
    Resolve official websites in a separate internal lookup.

    The provider-discovery JSON deliberately contains no URL fields. This
    follow-up grounded search returns one plain-text URL per numbered provider,
    and those URLs are used only for website/email verification.
    """
    results = [None] * len(providers)
    if not providers:
        return results

    numbered = "\n".join(
        f"{index + 1}. {(_safe_string(provider.get('name')) or '').strip()} "
        f"— {(_safe_string(provider.get('trade')) or '').strip()} "
        f"— {(_safe_string(provider.get('location')) or 'location unknown').strip()}"
        for index, provider in enumerate(providers)
    )
    prompt = f"""Use Google Search to find the official homepage for each listed provider.

Providers:
{numbered}

Return exactly one line for each numbered provider, in the same order, using this
format: NUMBER | URL
If an official homepage cannot be verified, return NUMBER | NONE.
Return plain text only, not JSON, markdown fences, explanations, or source lists.
Use only URLs supported by Google Search evidence. Do not invent or reconstruct URLs.
Prefer the provider's official domain, not directories or social profiles.
"""

    try:
        response = client.interactions.create(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            input=prompt,
            tools=[{"type": "google_search"}],
            generation_config={
                "thinking_level": "low",
                "max_output_tokens": max(512, len(providers) * 80),
            },
        )
        output = _safe_string(getattr(response, "output_text", None)) or ""
    except Exception as exc:
        print(
            "[external search] internal website lookup failed: "
            f"error={exc!r}",
            flush=True,
        )
        return results

    for line in output.splitlines():
        match = re.match(r"^\s*(\d+)\s*[|:.-]\s*(.*?)\s*$", line)
        if not match:
            continue
        index = int(match.group(1)) - 1
        value = match.group(2).strip().strip("`<>()[] ")
        if index < 0 or index >= len(providers) or not value:
            continue
        if value.upper() in {"NONE", "N/A", "UNKNOWN", "NULL"}:
            continue

        url_match = re.search(r"https?://[^\s<>\"']+", value, re.IGNORECASE)
        if not url_match:
            continue
        website = _is_valid_business_website(url_match.group(0).rstrip(".,;"))
        if website:
            results[index] = website

    return results


def _verify_provider_website(provider):
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
            website=website,
        )
    except Exception as exc:
        print(
            "[external search] website verification failed: "
            f"name={provider.get('name')!r}, "
            f"error={exc!r}",
            flush=True,
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
    results = [
        {"website": None, "email": None, "phone": None}
        for _ in providers
    ]

    indexes = []

    for index, provider in enumerate(providers):
        if not isinstance(provider, dict):
            continue

        if _is_valid_business_website(provider.get("website")):
            indexes.append(index)

    if not indexes:
        return results

    print(
        "[external search] verifying websites in parallel: "
        f"{len(indexes)}",
        flush=True,
    )

    with ThreadPoolExecutor(
        max_workers=MAX_PARALLEL_WEBSITE_CHECKS
    ) as executor:
        futures = {
            executor.submit(
                _verify_provider_website,
                providers[index],
            ): index
            for index in indexes
        }

        for future in as_completed(futures):
            index = futures[future]

            try:
                results[index] = future.result()
            except Exception as exc:
                print(
                    "[external search] verification error: "
                    f"{exc!r}",
                    flush=True,
                )

                results[index] = {
                    "website": _is_valid_business_website(
                        providers[index].get("website")
                    ),
                    "email": None,
                    "phone": None,
                }

    return results


# ============================================================
# LOCATION SEARCH
# ============================================================

def _location_search_tiers(location):
    location = _safe_string(location) or "the customer's local area"

    return [
        (
            "main_place",
            f"""
Search primarily in the exact target location:

{location}

Prioritise providers physically located there or providers
with explicit evidence that they serve this location.
Do not jump to distant cities.
""",
        ),
        (
            "surrounding_areas",
            f"""
The target location did not provide enough suitable providers.

Expand into nearby towns, villages, suburbs and districts
immediately surrounding {location}.

Prefer nearby providers and businesses that explicitly
serve {location}. Do not jump directly to distant major cities.
""",
        ),
        (
            "wider_local_region",
            f"""
Search the wider local region around {location}, including
additional nearby communities.

Continue prioritising geographical proximity and evidence
that providers serve {location}.
""",
        ),
        (
            "wider_service_area",
            f"""
Search a wider reasonable service area around {location}
only to find additional suitable providers.

Prefer providers that explicitly state they serve {location}.
Do not assume that every provider in a distant city serves it.
""",
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
    retry=False,
):
    excluded_text = ""

    if excluded_businesses:
        excluded_text = (
            "\n\nBusinesses already found. Do not return them again:\n"
            + "\n".join(
                f"- {name}"
                for name in list(excluded_businesses)[:100]
            )
        )

    retry_instruction = ""

    if retry:
        retry_instruction = """
The previous response was malformed or incomplete. Start a fresh response. Return no more than 5 providers. Return complete valid JSON only, without markdown fences, explanations or text outside the JSON object. Keep each field concise. Never copy a malformed URL; use null for any uncertain URL.
"""

    return f"""
You are finding REAL service providers for Matchly, a
general-purpose service-provider discovery platform.

REQUIRED SERVICES OR PROVIDER TYPES:
{trades_text}

These requirements are dynamically generated from the
customer's request. They are NOT restricted to property
maintenance, tradespeople or contractors.

Find providers appropriate to the actual requested services.
Depending on the request, a suitable provider might be a
business, independent professional, specialist company,
consultant, tutor, repair service or another legitimate
service provider.

Do not force every request into a property-maintenance
category. Do not substitute a vaguely related service for
the actual requested service.

Search batch: {batch_number}

{location_instruction}

Use Google Search grounding and current public web evidence.

We ultimately need up to {TARGET_CONTRACTORS} suitable
providers with publicly verifiable business email addresses.
Return a concise pool of up to 8 strong candidates in this batch. Prefer quality over quantity so the JSON stays complete.

{excluded_text}

{retry_instruction}

GEOGRAPHIC RULES:
- Follow the current geographic tier.
- Prioritise providers near the target location.
- Prefer explicit evidence that a provider serves the target.
- Do not assume a distant provider serves the target.
- Do not jump ahead to the next geographic tier.

RELEVANCE RULES:
- The provider must genuinely offer the requested service.
- Interpret provider types flexibly and semantically.
- A provider's actual service description may use different
  wording from the requested service.
- Do not reject a suitable provider just because its
  specialty uses a synonym or a more specific description.
- The "trade" field is a general provider specialty label.
  It can describe ANY legitimate service category.
- Never invent a provider or claim an unverified service.
- Do not include websites, URLs, source URLs, links, or citation URLs
  anywhere in the provider JSON. Website discovery is a separate internal step.

Return ONLY valid JSON in this format:

{{
  "providers": [
    {{
      "name": "Business or provider name",
      "trade": "Actual service or provider specialty",
      "location": "Verified location or null",
      "rating": 4.8,
      "review_count": 100,
      "availability": null,
      "phone": "Publicly listed phone number or null",
      "email": "Publicly listed email or null"
    }}
  ]
}}

FIELD RULES:
1. Only return real providers supported by search evidence.
2. Never invent a business, person, phone number or email address.
3. Return null for information that cannot be verified.
4. Do not include website, URL, source_url, link, or citation fields.
5. The phone and email must be publicly listed.
6. The location must be supported by search evidence.
7. Ratings and review counts must be supported by evidence.
8. Only return providers relevant to the requested services.
9. A provider must appear only once.
10. Do not return any business listed above.
11. Missing information must be null.
12. Do not output explanations or markdown.
"""


def _extract_provider_objects(output):
    """
    Recover complete provider objects independently from the
    providers array, even if the surrounding JSON is malformed.

    Malformed or incomplete individual objects are skipped.
    """
    if not output:
        return []

    marker = re.search(r'"providers"\s*:\s*\[', output)

    if not marker:
        return []

    start = marker.end()
    providers = []

    depth = 0
    object_start = None
    in_string = False
    escaped = False

    for index in range(start, len(output)):
        char = output[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            if depth == 0:
                object_start = index

            depth += 1

        elif char == "}":
            if depth > 0:
                depth -= 1

                if depth == 0 and object_start is not None:
                    raw_object = output[object_start:index + 1]

                    try:
                        provider = json.loads(raw_object)

                        if isinstance(provider, dict):
                            providers.append(provider)

                    except (json.JSONDecodeError, TypeError, ValueError):
                        pass

                    object_start = None

        elif char == "]" and depth == 0:
            break

    return providers


def _request_gemini_provider_batch(client, prompt):
    try:
        response = client.interactions.create(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            input=prompt,
            tools=[{"type": "google_search"}],
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
                                    "name": {"type": "string"},
                                    "trade": {"type": "string"},
                                    "location": {"type": ["string", "null"]},
                                    "rating": {"type": ["number", "null"]},
                                    "review_count": {"type": ["integer", "null"]},
                                    "availability": {"type": ["string", "null"]},
                                    "phone": {"type": ["string", "null"]},
                                    "email": {"type": ["string", "null"]},
                                },
                                "required": ["name", "trade"],
                                "additionalProperties": False,
                            },
                        }
                    },
                    "required": ["providers"],
                    "additionalProperties": False,
                },
            },
            generation_config={
                "thinking_level": "low",
                "max_output_tokens": 8192,
            },
        )

    except Exception as exc:
        print(
            "[external search] Gemini discovery error: "
            f"{exc!r}",
            flush=True,
        )
        raise RuntimeError(
            f"Gemini provider search failed: {exc}"
        ) from exc

    raw_output = getattr(response, "output_text", None)
    output = _clean_json_response(raw_output)

    if not output:
        raise ValueError(
            "Gemini returned an empty provider response"
        )

    data = _parse_provider_json(output)

    providers = None

    if isinstance(data, dict):
        parsed_providers = data.get("providers")

        if isinstance(parsed_providers, list):
            providers = parsed_providers

    if providers is None:
        providers = _extract_provider_objects(output)

        print(
            "[external search] recovered providers individually: "
            f"{len(providers)}",
            flush=True,
        )

    if not providers:
        preview = output[:300].replace("\n", " ")
        tail = output[-160:].replace("\n", " ")

        raise ValueError(
            "Gemini returned malformed provider JSON and no "
            "complete providers could be recovered. "
            f"response_length={len(output)}, "
            f"preview={preview!r}, tail={tail!r}"
        )

    allowed_fields = {
        "name",
        "trade",
        "location",
        "rating",
        "review_count",
        "availability",
        "phone",
        "email",
    }

    cleaned = []
    rejected = 0

    for provider in providers:
        if not isinstance(provider, dict):
            rejected += 1
            continue

        item = {
            key: provider.get(key)
            for key in allowed_fields
            if key in provider
        }

        for key in (
            "name",
            "trade",
            "location",
            "availability",
            "phone",
            "email",
        ):
            value = item.get(key)

            if value is not None and not isinstance(value, str):
                item[key] = None

            elif isinstance(value, str):
                item[key] = value.strip()[:300] or None

        item["rating"] = _safe_float(
            item.get("rating")
        )

        item["review_count"] = _safe_int(
            item.get("review_count")
        )

        if not item.get("name") or not item.get("trade"):
            rejected += 1
            continue

        cleaned.append(item)

    print(
        "[external search] provider JSON parsing complete: "
        f"valid={len(cleaned)}, rejected={rejected}",
        flush=True,
    )

    return cleaned


def _discover_provider_batch(
    client,
    trades_text,
    location_instruction,
    excluded_businesses,
    batch_number,
):
    for attempt in range(1, MAX_GEMINI_JSON_ATTEMPTS + 1):
        prompt = _build_discovery_prompt(
            trades_text=trades_text,
            location_instruction=location_instruction,
            excluded_businesses=excluded_businesses,
            batch_number=batch_number,
            retry=attempt > 1,
        )

        try:
            return _request_gemini_provider_batch(
                client=client,
                prompt=prompt,
            )

        except ValueError as exc:
            print(
                "[external search] invalid provider JSON: "
                f"attempt={attempt}, error={exc!r}",
                flush=True,
            )

            if attempt >= MAX_GEMINI_JSON_ATTEMPTS:
                raise RuntimeError(
                    "Gemini returned invalid provider JSON after retry.\n\n"
                    f"{exc}"
                ) from exc

    return []


# ============================================================
# MAIN SEARCH
# ============================================================

def search_external_workers(
    maintenance_request_id,
    required_trades,
    location=None,
    email_subject=None,
    email_html=None,
    email_text_body=None,
):
    """
    Discover general-purpose service providers.

    The existing parameter names remain unchanged for
    compatibility with maintenance.py and other callers.

    Providers must have a valid publicly listed business
    email. If email content is supplied, an email is sent
    immediately after the candidate is verified.
    """
    if not maintenance_request_id:
        raise ValueError(
            "maintenance_request_id is required"
        )

    service_requirements = _format_service_requirements(
        required_trades
    )

    if not service_requirements:
        return []

    location_text = (
        _safe_string(location)
        or "the customer's local area"
    )

    client = _get_gemini_client()

    location_tiers = _location_search_tiers(location_text)

    candidates = []
    seen_businesses = set()
    seen_emails = set()

    for tier_index, (tier_name, location_instruction) in enumerate(
        location_tiers
    ):
        if len(candidates) >= TARGET_CONTRACTORS:
            break

        print(
            "[external search] starting tier: "
            f"{tier_name!r}, "
            f"qualifying={len(candidates)}/{TARGET_CONTRACTORS}",
            flush=True,
        )

        tier_start_count = len(candidates)

        for batch_number in range(1, 3):
            if len(candidates) >= TARGET_CONTRACTORS:
                break

            print(
                "[external search] requesting provider batch: "
                f"tier={tier_name!r}, batch={batch_number}",
                flush=True,
            )

            providers = _discover_provider_batch(
                client=client,
                trades_text=service_requirements,
                location_instruction=location_instruction,
                excluded_businesses={
                    name for name, _specialty in seen_businesses
                },
                batch_number=batch_number,
            )

            prepared_providers = []

            for provider in providers:
                if not isinstance(provider, dict):
                    continue

                name = _safe_string(provider.get("name"))
                specialty = _normalise_trade(
                    provider.get("trade")
                )

                if not name or not specialty:
                    continue

                business_key = (
                    re.sub(r"\s+", " ", name.lower()),
                    specialty,
                )

                if business_key in seen_businesses:
                    continue

                seen_businesses.add(business_key)
                prepared_providers.append(provider)

            if not prepared_providers:
                continue

            internal_websites = _discover_provider_websites(
                client=client,
                providers=prepared_providers,
            )
            for provider, website in zip(prepared_providers, internal_websites):
                provider["_internal_website"] = website
                provider["website"] = website

            verification_results = (
                _verify_provider_websites_parallel(
                    prepared_providers
                )
            )

            for index, provider in enumerate(prepared_providers):
                if len(candidates) >= TARGET_CONTRACTORS:
                    break

                name = _safe_string(provider.get("name"))
                specialty = _normalise_trade(
                    provider.get("trade")
                )

                location_value = _safe_string(
                    provider.get("location")
                )
                rating = _safe_float(provider.get("rating"))
                review_count = _safe_int(
                    provider.get("review_count")
                )
                availability = _safe_string(
                    provider.get("availability")
                )

                verification = verification_results[index]

                website = verification.get("website")

                phone = (
                    _normalise_phone(provider.get("phone"))
                    or verification.get("phone")
                )

                email = (
                    verification.get("email")
                    or _normalise_email(provider.get("email"))
                )

                if not _is_valid_public_email(email):
                    print(
                        "[external search] rejected provider "
                        "without valid public email: "
                        f"name={name!r}",
                        flush=True,
                    )
                    continue

                if email in seen_emails:
                    continue

                seen_emails.add(email)

                email_send_result = None
                email_send_error = None
                reply_token = None

                if email_subject and email_html:
                    reply_token = secrets.token_hex(24)

                    reply_to = (
                        f"replies+{reply_token}@matchly-app.com"
                    )

                    print(
                        "[provider email] sending: "
                        f"name={name!r}, email={email!r}",
                        flush=True,
                    )

                    try:
                        email_send_result = send_email(
                            to=email,
                            subject=email_subject,
                            html=email_html,
                            reply_to=reply_to,
                        )

                    except Exception as exc:
                        email_send_error = str(exc)

                        print(
                            "[provider email] failed: "
                            f"name={name!r}, "
                            f"error={exc!r}",
                            flush=True,
                        )

                        continue

                external_id = (
                    f"gemini-web-{maintenance_request_id}-"
                    f"{len(candidates) + 1}"
                )

                candidate = ExternalWorkerCandidate(
                    maintenance_request_id=maintenance_request_id,
                    provider="gemini_web_search",
                    external_id=external_id,
                    name=name,
                    trade=specialty,
                    location=location_value,
                    rating=rating,
                    review_count=review_count,
                    availability=availability,
                    website=None,
                    phone=phone,
                    email=email,
                    source_url=None,
                )

                candidate._email_send_result = email_send_result
                candidate._email_send_error = email_send_error
                candidate._email_subject = email_subject
                candidate._email_html = email_html
                candidate._email_text_body = email_text_body
                candidate._email_recipient = email
                candidate._reply_token = reply_token

                candidates.append(candidate)

                print(
                    "[external search] QUALIFYING provider "
                    f"{len(candidates)}/{TARGET_CONTRACTORS}: "
                    f"name={name!r}, "
                    f"service={specialty!r}, "
                    f"location={location_value!r}, "
                    f"email={email!r}, "
                    f"tier={tier_name!r}",
                    flush=True,
                )

        tier_added = len(candidates) - tier_start_count

        print(
            "[external search] completed tier: "
            f"{tier_name!r}, added={tier_added}, "
            f"total={len(candidates)}/{TARGET_CONTRACTORS}",
            flush=True,
        )

        if len(candidates) >= TARGET_CONTRACTORS:
            break

        if tier_index < len(location_tiers) - 1:
            print(
                "[external search] expanding to next geographic tier",
                flush=True,
            )

    print(
        "[external search] final qualifying providers: "
        f"{len(candidates)}/{TARGET_CONTRACTORS}",
        flush=True,
    )

    return candidates[:TARGET_CONTRACTORS]


# ============================================================
# BACKWARDS-COMPATIBLE ENTRY POINT
# ============================================================

def find_contractors_with_gemini(
    maintenance_request_id,
    required_trades,
    location=None,
    email_subject=None,
    email_html=None,
    email_text_body=None,
):
    return search_external_workers(
        maintenance_request_id=maintenance_request_id,
        required_trades=required_trades,
        location=location,
        email_subject=email_subject,
        email_html=email_html,
        email_text_body=email_text_body,
    )
