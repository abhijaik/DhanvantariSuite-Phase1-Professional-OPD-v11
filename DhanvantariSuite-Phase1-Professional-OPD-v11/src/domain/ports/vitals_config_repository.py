from abc import ABC, abstractmethod
from typing import Optional

class VitalsConfigRepository(ABC):
    @abstractmethod
    def get_recorder_role(self, tenant_id: str, branch_id: str) -> str:
        pass

    @abstractmethod
    def set_recorder_role(self, tenant_id: str, branch_id: str, role: str) -> None:
        pass
