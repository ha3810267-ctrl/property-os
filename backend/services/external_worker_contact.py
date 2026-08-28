
import os

from google import genai

from backend.services.email import send_email


def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured"
        )

    return genai.Client(
        api_key=api_key
    )


def generate_contractor_email(
    contractor_name,
    business_name,
    trade,
    maintenance_description,
    property_location
):
    """
    Generate a professional contractor enquiry email
    using Gemini.
    """

    if not business_name:
        raise ValueError(
            "Contractor business name is required"
        )

    if not trade:
        raise ValueError(
            "Contractor trade is required"
        )

    if not maintenance_description:
        raise ValueError(
            "Maintenance description is required"
        )

    client = _get_gemini_client()

    contractor_display_name = (
        contractor_name
        if contractor_name
        else business_name
    )

    location_text = (
        property_location
        if property_location
        else "the relevant property"
    )

    prompt = f"""
You are an email assistant for a professional
property management platform.

Write a concise professional email to an external
contractor about a maintenance request.

Contractor:
{contractor_display_name}

Business:
{business_name}

Trade:
{trade}

Property location:
{location_text}

Maintenance issue:
{maintenance_description}

The email should:

- Clearly explain the maintenance issue.
- Mention the property location.
- Ask whether they can take the job.
- Ask about their availability.
- Ask for an estimated price or quote.
- Be professional and concise.
- Do not invent any facts.
- Do not invent dates or times.
- Do not claim the job has been approved.
- Do not include a subject line.
- Return ONLY the email body.
"""

    try:
        response = client.models.generate_content(
            model=os.getenv(
                "GEMINI_MODEL",
                "gemini-2.5-flash"
            ),
            contents=prompt
        )

    except Exception as exc:
        raise RuntimeError(
            f"Gemini contractor email generation failed: {exc}"
        ) from exc

    email_body = getattr(
        response,
        "text",
        None
    )

    if not email_body:
        raise RuntimeError(
            "Gemini returned an empty contractor email"
        )

    return email_body.strip()


def contact_contractor(
    contractor,
    maintenance_description,
    property_location
):
    """
    Generate and send a contractor enquiry email.

    Returns the generated email information.
    """

    if not contractor.email:
        raise ValueError(
            "Contractor does not have a verified email address"
        )

    email_body = generate_contractor_email(
        contractor_name=contractor.name,
        business_name=contractor.name,
        trade=contractor.trade,
        maintenance_description=maintenance_description,
        property_location=property_location
    )

    subject = (
        f"Maintenance enquiry - {contractor.trade}"
    )

    send_email(
        to=contractor.email,
        subject=subject,
        html=email_body.replace(
            "\n",
            "<br>"
        )
    )

    return {
        "email": contractor.email,
        "subject": subject,
        "body": email_body
    }
