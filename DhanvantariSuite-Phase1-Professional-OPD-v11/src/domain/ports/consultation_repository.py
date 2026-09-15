from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.models.consultation import Consultation

class ConsultationRepository(ABC):
    @abstractmethod
    def save(self, consultation: Consultation) -> Consultation:
        pass

    @abstractmethod
    def find_by_id(self, consultation_id: str, tenant_id: str) -> Optional[Consultation]:
        pass

    @abstractmethod
    def find_by_appointment_id(self, appointment_id: str, tenant_id: str) -> Optional[Consultation]:
        pass

    @abstractmethod
    def list_by_patient(self, patient_id: str, tenant_id: str) -> List[Consultation]:
        pass
