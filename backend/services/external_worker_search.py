import json
import os
import re
import socket
from html import unescape
from urllib.parse import (
    urljoin,
    urlparse,
)
from urllib.request import (
    Request,
    urlopen,
)

from google import genai

from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)


EMAIL_PATTERN = re.compile(
    r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}",
    re.IGNORECASE
)

CONTACT_PAGE_KEYWORDS = (
    "contact",
    "contact-us",
    "contactus",
    "get-in-touch",
    "getintouch",
    "enquir",
    "enquir",
    "about",
)

MAX_PAGE_BYTES = 2_000_000
REQUEST_TIMEOUT = 300

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
    value = _safe_string(value)

    if not value:
        return None

    value = unescape(value).strip()

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

    # Reject obviously broken addresses
    if (
        ".." in email
        or email.startswith(".")
        or email.endswith(".")
    ):
        return None

    return email


def _is_public_hostname(hostname):
    """
    Prevent website fetching from resolving to local/private
    network addresses.

    This is important because the URL ultimately comes from
    external search results.
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
            ip_obj = socket.inet_pton(
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

                # Reject loopback/link-local/private IPv6
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
    url = _safe_string(url)

    if not url:
        return None

    if not url.startswith(
        ("http://", "https://")
    ):
        url = "https://" + url

    parsed = urlparse(url)

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


def _fetch_web_page(url):
    """
    Fetch a public website page.

    Returns decoded HTML or None.
    """

    url = _normalise_url(url)

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
                )
                .lower()
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
    Extract emails from visible HTML and mailto links.

    Handles basic obfuscation such as:
        name [at] domain.com
        name (at) domain.com
        name at domain.com
    """

    if not html:
        return []

    html = unescape(
        html
    )

    found = []

    # Normal emails
    for match in EMAIL_PATTERN.findall(
        html
    ):
        email = _normalise_email(
            match
        )

        if email and email not in found:
            found.append(email)

    # mailto links that may have odd HTML formatting
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

        if email and email not in found:
            found.append(email)

    # Basic text obfuscation
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

            if isinstance(
                match,
                tuple
            ):
                email = (
                    f"{match[0]}@{match[1]}"
                )
            else:
                email = match

            email = _normalise_email(
                email
            )

            if email and email not in found:
                found.append(email)

    return found


def _extract_links(html, base_url):
    """
    Find links that look like contact/about/enquiry pages.
    """

    if not html:
        return []

    links = []

    pattern = re.compile(
        r'<a\b[^>]*href\s*=\s*'
        r'["\']([^"\']+)["\'][^>]*>'
        r'(.*?)'
        r'</a>',
        re.IGNORECASE | re.DOTALL
    )

    for href, anchor_text in pattern.findall(
        html
    ):

        href = unescape(
            href
        ).strip()

        anchor_text = re.sub(
            r"<[^>]+>",
            " ",
            anchor_text
        )

        combined = (
            f"{href} {anchor_text}"
        ).lower()

        if not any(
            keyword in combined
            for keyword in CONTACT_PAGE_KEYWORDS
        ):
            continue

        absolute_url = urljoin(
            base_url,
            href
        )

        absolute_url = _normalise_url(
            absolute_url
        )

        if not absolute_url:
            continue

        base_host = (
            urlparse(base_url).hostname
            or ""
        ).lower()

        link_host = (
            urlparse(absolute_url).hostname
            or ""
        ).lower()

        # Only follow links on the same domain
        if link_host != base_host:
            continue

        if absolute_url not in links:
            links.append(
                absolute_url
            )

    return links[:5]


def _find_email_on_website(
    website,
    business_name=None
):
    """
    Search a contractor's public website for a business
    email.

    First checks the supplied website, then likely
    Contact/About/Enquiry pages.
    """

    website = _normalise_url(
        website
    )

    if not website:
        return None

    print(
        "[external search] checking website for email: "
        f"{website!r}",
        flush=True
    )

    html = _fetch_web_page(
        website
    )

    if not html:
        return None

    emails = _extract_emails_from_html(
        html
    )

    if emails:

        print(
            "[external search] email found on homepage: "
            f"{emails[0]!r}",
            flush=True
        )

        return emails[0]

    contact_links = _extract_links(
        html,
        website
    )

    for contact_url in contact_links:

        print(
            "[external search] checking contact page: "
            f"{contact_url!r}",
            flush=True
        )

        contact_html = _fetch_web_page(
            contact_url
        )

        if not contact_html:
            continue

        emails = _extract_emails_from_html(
            contact_html
        )

        if emails:

            print(
                "[external search] email found on contact page: "
                f"{emails[0]!r}",
                flush=True
            )

            return emails[0]

    # Some websites do not expose a clickable contact
    # link in their HTML. Try common paths directly.
    parsed = urlparse(
        website
    )

    base = (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
    )

    common_paths = [
        "/contact",
        "/contact-us",
        "/contactus",
        "/get-in-touch",
        "/enquiries",
        "/about",
    ]

    tried = set(
        contact_links
    )

    for path in common_paths:

        contact_url = _normalise_url(
            urljoin(
                base + "/",
                path.lstrip("/")
            )
        )

        if not contact_url:
            continue

        if contact_url in tried:
            continue

        tried.add(
            contact_url
        )

        contact_html = _fetch_web_page(
            contact_url
        )

        if not contact_html:
            continue

        emails = _extract_emails_from_html(
            contact_html
        )

        if emails:

            print(
                "[external search] email found on common "
                f"contact path: {emails[0]!r}",
                flush=True
            )

            return emails[0]

    print(
        "[external search] no public email found on website: "
        f"{website!r}",
        flush=True
    )

    return None


def _discover_email(
    provider,
    website,
):
    """
    Determine the contractor email.

    Priority:

    1. Email found directly by Gemini
    2. Email extracted from contractor website
    """

    gemini_email = _normalise_email(
        provider.get("email")
    )

    if gemini_email:

        print(
            "[external search] using Gemini verified email "
            f"for {provider.get('name')!r}: "
            f"{gemini_email!r}",
            flush=True
        )

        return gemini_email

    website_email = _find_email_on_website(
        website=website,
        business_name=provider.get("name")
    )

    if website_email:
        return website_email

    return None


def search_external_workers(
    maintenance_request_id,
    required_trades,
    location=None
):
    """
    Discover real external service providers using Gemini
    with Google Search grounding.

    Gemini handles contractor discovery and ranking.

    After discovery, the backend additionally checks each
    contractor's public website and contact pages for a
    publicly listed email address.

    Returns new ExternalWorkerCandidate objects.

    Candidates are not selected or contacted here.
    Ranking and outreach are handled by the maintenance
    request workflow.
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
You are a service-provider research assistant for a
property maintenance platform.

Find real external businesses that could carry out
property maintenance work.

Required trades:
{trades_text}

Target location:
{location_text}

Use Google Search to research current public web
information.

Return ONLY a JSON object.

Required structure:

{{
    "providers": [
        {{
            "name": "Business display name",
            "trade": "matching trade",
            "location": "business location",
            "rating": 4.8,
            "review_count": 120,
            "availability": "Available soon",
            "website": "https://example.com",
            "phone": "01234567890",
            "email": "hello@example.com",
            "source_url": "https://example.com/source"
        }}
    ]
}}

Rules:

1. Only include real businesses supported by web
   search evidence.

2. Never invent a business.

3. Never invent contact information.

4. Never invent ratings or review counts.

5. If a value cannot be verified, return null.

6. Only return businesses relevant to the requested
   trades.

7. Prefer businesses close to the target location.

8. Include up to 10 strong candidates.

9. A business may appear only once.

10. "trade" must correspond to one of the requested
    trades.

11. Use publicly available business contact details
    where available.

12. source_url should identify the web source used
    to support the business information.

13. Do not return markdown.

14. Do not return explanations outside the JSON.
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

        raise RuntimeError(
            f"Gemini provider search failed: {exc}"
        ) from exc

    try:
        response_debug = response.model_dump(
            exclude_none=True
        )
    except AttributeError:
        response_debug = repr(response)

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

        print(
            "[external search] Gemini JSON root was not an object: "
            f"{type(data).__name__}",
            flush=True
        )

        return []

    providers = data.get(
        "providers",
        []
    )

    if not isinstance(
        providers,
        list
    ):

        print(
            "[external search] Gemini 'providers' was not a list: "
            f"{type(providers).__name__}",
            flush=True
        )

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

            print(
                "[external search] rejected provider: not an object: "
                f"{provider!r}",
                flush=True
            )

            continue

        name = _safe_string(
            provider.get("name")
        )

        if not name:

            print(
                "[external search] rejected provider: missing name: "
                f"{provider!r}",
                flush=True
            )

            continue

        trade = _normalise_trade(
            provider.get("trade")
        )

        if not trade:

            print(
                "[external search] rejected provider: missing trade: "
                f"name={name!r}",
                flush=True
            )

            continue

        if trade not in trade_names:

            print(
                "[external search] rejected provider: trade mismatch: "
                f"name={name!r}, trade={trade!r}, "
                f"required={trade_names!r}",
                flush=True
            )

            continue

        location_value = _safe_string(
            provider.get("location")
        )

        if not location_value:
            location_value = location_text

        business_key = (
            name.lower(),
            trade
        )

        if business_key in seen_businesses:

            print(
                "[external search] rejected provider: duplicate in Gemini "
                f"response: name={name!r}, trade={trade!r}",
                flush=True
            )

            continue

        seen_businesses.add(
            business_key
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

        website = _safe_string(
            provider.get("website")
        )

        phone = _safe_string(
            provider.get("phone")
        )

        # -------------------------------------------------
        # NEW:
        # Search the contractor website for an email.
        # -------------------------------------------------

        email = _discover_email(
            provider=provider,
            website=website
        )

        source_url = _safe_string(
            provider.get("source_url")
        )

        if email:

            print(
                "[external search] final contractor email: "
                f"name={name!r}, email={email!r}",
                flush=True
            )

        else:

            print(
                "[external search] no public email found: "
                f"name={name!r}",
                flush=True
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
            contact_status="discovered"
        )

        candidates.append(
            candidate
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