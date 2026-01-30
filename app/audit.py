from sqlalchemy.orm import Session
from app.models import AuditLog


def write_audit_log(
    db: Session,
    actor_email: str | None,
    action: str,
    endpoint: str,
    status: str,
    ip_address: str | None = None,
):
    log = AuditLog(
        actor_email=actor_email,
        action=action,
        endpoint=endpoint,
        status=status,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
