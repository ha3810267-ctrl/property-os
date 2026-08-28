
import os
from datetime import datetime, timezone

from backend.database import db
from backend.models.external_worker_candidate import (
    ExternalWorkerCandidate
)
from backend.models.maintenance_request import MaintenanceRequest
from backend.services.email import send_email


def send_contractor_request(
    candidate: ExternalWorkerCandidate,
    maintenance_request: MaintenanceRequest
):
    """
    Send a maintenance job enquiry to an external contractor.

    The contractor is not automatically selected or hired.
    This only sends an enquiry and records the outreach state.
    """

    if not candidate:
        raise ValueError(
            "Contractor candidate is required"
        )

    if not maintenance_request:
        raise ValueError(
            "Maintenance request is required"
        )

    if not candidate.email:
        raise ValueError(
            "Contractor does not have a verified email address"
        )

    subject = (
        f"Maintenance Request - "
        f"{maintenance_request.category or 'Property Maintenance'}"
    )

    html = f"""
    <html>
        <body>
            <h2>Maintenance Request</h2>

            <p>Hello {candidate.name},</p>

            <p>
                We are contacting you regarding a maintenance
                request that may require your services.
            </p>

            <p>
                <strong>Issue:</strong><br>
                {maintenance_request.description}
            </p>

            <p>
                <strong>Required trade:</strong><br>
                {candidate.trade}
            </p>

            <p>
                Please reply to this email with:
            </p>

            <ul>
                <li>Whether you can take the job</li>
                <li>Your estimated price</li>
                <li>Your earliest available start date</li>
                <li>Any relevant information about the work</li>
            </ul>

            <p>
                This is an enquiry only and does not constitute
                an acceptance of the job.
            </p>

            <p>
                Regards,<br>
                Property Management
            </p>
        </body>
    </html>
    """

    try:
        response = send_email(
            to=candidate.email,
            subject=subject,
            html=html
        )

    except Exception as exc:
        candidate.contact_status = "email_failed"
        candidate.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        raise RuntimeError(
            f"Failed to contact contractor: {exc}"
        ) from exc

    candidate.contact_status = "contacted"
    candidate.email_sent_at = datetime.now(timezone.utc)
    candidate.updated_at = datetime.now(timezone.utc)

    db.session.commit()

    return response

