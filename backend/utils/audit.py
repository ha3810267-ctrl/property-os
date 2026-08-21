from backend.database import db
from backend.models.audit_log import AuditLog


def create_audit_log(
    user,
    action,
    resource_type,
    resource_id=None
):
    audit_log = AuditLog(
        organisation_id=user.organisation_id,
        user_id=user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id
    )

    db.session.add(audit_log)

    return audit_log