from abc import ABC, abstractmethod
from typing import Optional
from src.domain.models.clinic_settings import ClinicSettings

class ClinicSettingsRepository(ABC):
    @abstractmethod
    def save(self, settings: ClinicSettings) -> ClinicSettings:
        pass

    @abstractmethod
    def get(self, tenant_id: str, branch_id: str) -> Optional[ClinicSettings]:
        pass
