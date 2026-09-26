
import os

import resend
from dotenv import load_dotenv


load_dotenv()


RESEND_API_KEY = os.getenv("RESEND_API_KEY")

EMAIL_FROM = os.getenv(
    "EMAIL_FROM",
    "Property SaaS <onboarding@resend.dev>"
)

EMAIL_REPLY_TO = os.getenv(
    "EMAIL_REPLY_TO"
)


def send_email(
    to,
    subject,
    html
):
    if not RESEND_API_KEY:
        raise RuntimeError(
            "RESEND_API_KEY is not configured"
        )

    if not EMAIL_REPLY_TO:
        raise RuntimeError(
            "EMAIL_REPLY_TO is not configured"
        )

    resend.api_key = RESEND_API_KEY

    return resend.Emails.send({
        "from": EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "reply_to": EMAIL_REPLY_TO,
        "html": html
    })

