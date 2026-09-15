import uuid
from datetime import datetime
from typing import Optional
from src.domain.models.vitals import PatientVitals
from src.domain.ports.vitals_repository import VitalsRepository
from src.domain.ports.vitals_config_repository import VitalsConfigRepository

class VitalsService:
    def __init__(self, vitals_repo: VitalsRepository, config_repo: VitalsConfigRepository):
        self.vitals_repo = vitals_repo
        self.config_repo = config_repo

    def get_recorder_role(self, tenant_id: str, branch_id: str) -> str:
        return self.config_repo.get_recorder_role(tenant_id, branch_id)

    def set_recorder_role(self, tenant_id: str, branch_id: str, role: str) -> None:
        self.config_repo.set_recorder_role(tenant_id, branch_id, role)

    def record_vitals(
        self,
        tenant_id: str,
        branch_id: str,
        appointment_id: str,
        blood_pressure: Optional[str],
        weight: Optional[float],
        height: Optional[float],
        temperature: Optional[float],
        pulse: Optional[int],
        spo2: Optional[int],
        respiratory_rate: Optional[int],
        recorded_by: str
    ) -> PatientVitals:
        # Calculate BMI automatically if weight (kg) and height (cm) are provided
        bmi = None
        if weight and height and height > 0:
            height_meters = height / 100.0
            bmi = round(weight / (height_meters ** 2), 2)

        existing = self.vitals_repo.find_by_appointment_id(appointment_id, tenant_id)
        vitals_id = existing.id if existing else str(uuid.uuid4())

        vitals = PatientVitals(
            id=vitals_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            appointment_id=appointment_id,
            blood_pressure=blood_pressure,
            weight=weight,
            height=height,
            bmi=bmi,
            temperature=temperature,
            pulse=pulse,
            spo2=spo2,
            respiratory_rate=respiratory_rate,
            recorded_by=recorded_by,
            recorded_at=datetime.utcnow()
        )
        return self.vitals_repo.save(vitals)

    def get_vitals_by_appointment(self, appointment_id: str, tenant_id: str) -> Optional[PatientVitals]:
        return self.vitals_repo.find_by_appointment_id(appointment_id, tenant_id)
