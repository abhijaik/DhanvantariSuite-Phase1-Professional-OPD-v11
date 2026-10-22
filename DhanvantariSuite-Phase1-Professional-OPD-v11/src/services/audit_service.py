import uuid
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from src.domain.models.audit_log import AuditLog
from src.adapters.db.repositories import SQLAlchemyAuditLogRepository

logger = logging.getLogger("dhanvantari.audit")

class AuditService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = SQLAlchemyAuditLogRepository(session)

    def record(
        self,
        tenant_id: str,
        branch_id: str,
        user_id: str,
        user_role: Optional[str],
        action: str,
        module: str,
        record_id: str,
        summary: str,
        ip_address: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Records an immutable audit log entry for HIPAA / DPDP compliance.
        Guarantees that audit logging failures do not break primary clinical workflows.
        """
        try:
            log = AuditLog(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id or "local-clinic",
                branch_id=branch_id or "default-branch",
                user_id=user_id or "anonymous",
                user_role=user_role,
                action=action,
                module=module,
                record_id=str(record_id),
                ip_address=ip_address,
                timestamp=datetime.utcnow(),
                summary=summary
            )
            saved = self.repo.save(log)
            self.session.commit()
            return saved
        except Exception as e:
            logger.error(f"Failed to record audit log: action={action}, module={module}, error={str(e)}")
            return None

    def query(
        self,
        tenant_id: str,
        branch_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        module: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        return self.repo.list_logs(
            tenant_id=tenant_id,
            branch_id=branch_id,
            from_date=from_date,
            to_date=to_date,
            module=module,
            action=action,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
