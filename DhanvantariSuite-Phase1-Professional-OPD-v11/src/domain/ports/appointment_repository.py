from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import date
from src.domain.models.appointment import Appointment

class AppointmentRepository(ABC):
    @abstractmethod
    def save(self, appointment: Appointment) -> Appointment:
        pass

    @abstractmethod
    def find_by_id(self, appointment_id: str, tenant_id: str) -> Optional[Appointment]:
        pass

    @abstractmethod
    def list_by_date_and_doctor(self, appointment_date: date, doctor_id: str, tenant_id: str, branch_id: str) -> List[Appointment]:
        pass

    @abstractmethod
    def list_queue(self, appointment_date: date, tenant_id: str, branch_id: str) -> List[Appointment]:
        pass

    @abstractmethod
    def get_next_token_value(self, appointment_date: date, doctor_id: str, tenant_id: str, branch_id: str) -> int:
        # Generates auto-incrementing token value for the day/doctor
        pass
