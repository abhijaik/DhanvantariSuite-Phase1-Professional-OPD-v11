import uuid
from datetime import date, time, datetime
from typing import List, Optional

from src.domain.models.appointment import Appointment, AppointmentStatus
from src.domain.ports.appointment_repository import AppointmentRepository

class QueueService:
    def __init__(self, appointment_repo: AppointmentRepository):
        self.appointment_repo = appointment_repo

    def book_appointment(
        self,
        tenant_id: str,
        branch_id: str,
        patient_id: str,
        doctor_id: str,
        appointment_date: date,
        scheduled_time: time,
        visit_type: str,
        consultation_type: str,
        notes: Optional[str] = "",
        consultation_subtype: Optional[str] = None,
        referred_by_type: Optional[str] = None,
        referred_by_name: Optional[str] = None
    ) -> Appointment:
        # Queue tokens are used only for multi-doctor OPD. The caller passes a resolved doctor and
        # the API decides whether the branch needs a token. This service keeps the token value explicit.
        queue_token = ""

        appointment = Appointment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            scheduled_time=scheduled_time,
            status=AppointmentStatus.BOOKED,
            queue_token=queue_token,
            visit_type=visit_type,
            consultation_type=consultation_type,
            consultation_subtype=consultation_subtype,
            referred_by_type=referred_by_type,
            referred_by_name=referred_by_name,
            notes=notes or "",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return self.appointment_repo.save(appointment)

    def check_in_patient(self, appointment_id: str, tenant_id: str) -> Appointment:
        """Move appointment status from SCHEDULED/BOOKED to IN_QUEUE."""
        appointment = self.appointment_repo.find_by_id(appointment_id, tenant_id)
        if not appointment:
            raise ValueError("Appointment not found")
        if appointment.status not in [AppointmentStatus.SCHEDULED, AppointmentStatus.BOOKED]:
            raise ValueError(f"Cannot check in appointment with status {appointment.status}")

        appointment.status = AppointmentStatus.IN_QUEUE
        appointment.updated_at = datetime.utcnow()
        return self.appointment_repo.save(appointment)

    def start_consultation(self, appointment_id: str, tenant_id: str) -> Appointment:
        """Move appointment status to CONSULTING when doctor calls patient in."""
        appointment = self.appointment_repo.find_by_id(appointment_id, tenant_id)
        if not appointment:
            raise ValueError("Appointment not found")
        
        appointment.status = AppointmentStatus.CONSULTING
        appointment.updated_at = datetime.utcnow()
        return self.appointment_repo.save(appointment)

    def get_live_queue(self, tenant_id: str, branch_id: str, query_date: Optional[date] = None) -> List[Appointment]:
        if not query_date:
            query_date = date.today()
        return self.appointment_repo.list_queue(query_date, tenant_id, branch_id)
