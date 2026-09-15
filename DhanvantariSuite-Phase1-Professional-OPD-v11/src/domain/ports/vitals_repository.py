from abc import ABC, abstractmethod
from typing import Optional
from src.domain.models.vitals import PatientVitals

class VitalsRepository(ABC):
    @abstractmethod
    def save(self, vitals: PatientVitals) -> PatientVitals:
        pass

    @abstractmethod
    def find_by_appointment_id(self, appointment_id: str, tenant_id: str) -> Optional[PatientVitals]:
        pass
