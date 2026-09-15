from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from src.domain.models.audit_log import AuditLog

class AuditLogRepository(ABC):
    @abstractmethod
    def save(self, log: AuditLog) -> AuditLog:
        pass

    @abstractmethod
    def list_logs(self, tenant_id: str, branch_id: str, from_date: datetime, to_date: datetime) -> List[AuditLog]:
        pass
