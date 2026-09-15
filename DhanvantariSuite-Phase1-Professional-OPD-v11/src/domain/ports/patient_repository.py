from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.models.patient import Patient

class PatientRepository(ABC):
    @abstractmethod
    def save(self, patient: Patient) -> Patient:
        pass

    @abstractmethod
    def find_by_id(self, patient_id: str, tenant_id: str) -> Optional[Patient]:
        pass

    @abstractmethod
    def find_by_mobile(self, mobile_normalized: str, tenant_id: str) -> Optional[Patient]:
        pass

    @abstractmethod
    def search(self, query: str, tenant_id: str) -> List[Patient]:
        pass
