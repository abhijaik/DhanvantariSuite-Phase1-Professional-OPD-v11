from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models.sync_log import SyncLog

class SyncLogRepository(ABC):
    @abstractmethod
    def save(self, sync_log: SyncLog) -> SyncLog:
        pass

    @abstractmethod
    def get_unsynced(self, tenant_id: str, limit: int = 100) -> List[SyncLog]:
        pass

    @abstractmethod
    def mark_as_synced(self, log_ids: List[str], tenant_id: str) -> None:
        pass
