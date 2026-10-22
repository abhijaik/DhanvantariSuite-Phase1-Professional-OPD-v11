from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from src.domain.models.audit_log import AuditLog

class AuditLogRepository(ABC):
    @abstractmethod
    def save(self, log: AuditLog) -> AuditLog:
        pass

    @abstractmethod
    def list_logs(
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
        pass
