import uuid
from datetime import date, datetime
from typing import List, Optional

from src.domain.models.consultation import Consultation, PrescriptionItem
from src.domain.models.appointment import AppointmentStatus
from src.domain.ports.consultation_repository import ConsultationRepository
from src.domain.ports.appointment_repository import AppointmentRepository

class ConsultationService:
    def __init__(
        self,
        consultation_repo: ConsultationRepository,
        appointment_repo: AppointmentRepository,
        vitals_repo = None
    ):
        self.consultation_repo = consultation_repo
        self.appointment_repo = appointment_repo
        self.vitals_repo = vitals_repo

    def complete_consultation(
        self,
        tenant_id: str,
        branch_id: str,
        appointment_id: str,
        symptoms: List[str],
        diagnosis: str,
        prescription: List[PrescriptionItem],
        blood_pressure: Optional[str] = None,
        weight: Optional[float] = None,
        height: Optional[float] = None,
        bmi: Optional[float] = None,
        temperature: Optional[float] = None,
        pulse_rate: Optional[int] = None,
        spo2: Optional[int] = None,
        respiratory_rate: Optional[int] = None,
        follow_up_date: Optional[date] = None,
        notes: Optional[str] = "",
        consultation_type: Optional[str] = None,
        consultation_subtype: Optional[str] = None
    ) -> Consultation:
        # Find corresponding appointment
        appointment = self.appointment_repo.find_by_id(appointment_id, tenant_id)
        if not appointment:
            raise ValueError("Appointment not found")

        # Load pre-recorded vitals from receptionist/nurse if any fields are missing
        if self.vitals_repo:
            pre_vitals = self.vitals_repo.find_by_appointment_id(appointment_id, tenant_id)
            if pre_vitals:
                blood_pressure = blood_pressure or pre_vitals.blood_pressure
                weight = weight or pre_vitals.weight
                height = height or pre_vitals.height
                bmi = bmi or pre_vitals.bmi
                temperature = temperature or pre_vitals.temperature
                pulse_rate = pulse_rate or pre_vitals.pulse
                spo2 = spo2 or pre_vitals.spo2
                respiratory_rate = respiratory_rate or pre_vitals.respiratory_rate

        # Auto-calculate BMI if weight and height are provided but BMI is missing
        if not bmi and weight and height and height > 0:
            height_meters = height / 100.0
            bmi = round(weight / (height_meters ** 2), 2)

        # Fallback to appointment's consultation type/subtype if not explicitly sent in consultation payload
        final_type = consultation_type or appointment.consultation_type
        final_subtype = consultation_subtype or appointment.consultation_subtype

        # Create consultation
        consultation = Consultation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            appointment_id=appointment_id,
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            consultation_type=final_type,
            consultation_subtype=final_subtype,
            symptoms=symptoms,
            diagnosis=diagnosis,
            prescription=prescription,
            blood_pressure=blood_pressure,
            weight=weight,
            height=height,
            bmi=bmi,
            temperature=temperature,
            pulse_rate=pulse_rate,
            spo2=spo2,
            respiratory_rate=respiratory_rate,
            follow_up_date=follow_up_date,
            notes=notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        saved_consultation = self.consultation_repo.save(consultation)

        # Update appointment status to COMPLETED (which queues for billing)
        appointment.status = AppointmentStatus.COMPLETED
        appointment.updated_at = datetime.utcnow()
        self.appointment_repo.save(appointment)

        return saved_consultation

    def get_patient_history(self, patient_id: str, tenant_id: str) -> List[Consultation]:
        return self.consultation_repo.list_by_patient(patient_id, tenant_id)
