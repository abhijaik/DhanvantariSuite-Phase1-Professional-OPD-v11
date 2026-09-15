import uuid
from datetime import date, datetime
from typing import Optional, List

from src.domain.models.patient import Patient
from src.domain.ports.patient_repository import PatientRepository

class PatientService:
    def __init__(self, patient_repo: PatientRepository):
        self.patient_repo = patient_repo

    def register_patient(
        self,
        tenant_id: str,
        branch_id: str,
        full_name: str,
        mobile: str,
        date_of_birth: date,
        age: int,
        gender: str,
        address: str,
        registration_date: Optional[date] = None,
        alternate_number: Optional[str] = None,
        email: Optional[str] = None,
        blood_group: Optional[str] = None,
        marital_status: Optional[str] = None,
        emergency_contact: Optional[str] = None,
        allergies: Optional[str] = "",
        medical_notes: Optional[str] = "",
        referred_by: Optional[str] = None
    ) -> Patient:
        # Normalize mobile number
        mobile_normalized = Patient.normalize_mobile(mobile)

        # Duplicate prevention check
        existing = self.patient_repo.find_by_mobile(mobile_normalized, tenant_id)
        if existing:
            raise ValueError(f"Patient with mobile {mobile_normalized} is already registered under ID {existing.patient_number}")

        # Generate a unique patient number based on list length/count or UUID snippet
        import random
        random_suffix = random.randint(1000, 9999)
        patient_num = f"P-{datetime.now().strftime('%y%m%d')}-{random_suffix}"

        patient = Patient(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            patient_number=patient_num,
            registration_date=registration_date or date.today(),
            full_name=full_name,
            date_of_birth=date_of_birth,
            age=age,
            gender=gender,
            mobile_normalized=mobile_normalized,
            alternate_number=alternate_number,
            email=email,
            address=address,
            blood_group=blood_group,
            marital_status=marital_status,
            emergency_contact=emergency_contact,
            allergies=allergies or "",
            medical_notes=medical_notes or "",
            referred_by=referred_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return self.patient_repo.save(patient)

    def find_patient(self, patient_id: str, tenant_id: str) -> Optional[Patient]:
        return self.patient_repo.find_by_id(patient_id, tenant_id)

    def search_patients(self, query: str, tenant_id: str) -> List[Patient]:
        return self.patient_repo.search(query, tenant_id)
