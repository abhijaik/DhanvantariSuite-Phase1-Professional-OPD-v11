from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from typing import List, Optional

from src.adapters.api.dependencies import get_db, require_role, require_clinical_edit, require_clinical_view
from src.adapters.db.repositories import (
    SQLAlchemyConsultationRepository, SQLAlchemyAppointmentRepository, SQLAlchemyPatientRepository,
    SQLAlchemyVitalsRepository, SQLAlchemyUserRepository, SQLAlchemyClinicSettingsRepository
)
from src.adapters.docgen.pdf_generator import PDFGeneratorAdapter
from src.services.consultation_service import ConsultationService
from src.domain.models.user import UserRole, User
from src.domain.models.consultation import Consultation, PrescriptionItem

router = APIRouter(prefix="/api/consultations", tags=["Consultations"])

class ConsultationCompleteRequest(BaseModel):
    appointment_id: str
    symptoms: List[str]
    diagnosis: str
    prescription: List[PrescriptionItem]
    blood_pressure: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    bmi: Optional[float] = None
    temperature: Optional[float] = None
    pulse_rate: Optional[int] = None
    spo2: Optional[int] = None
    respiratory_rate: Optional[int] = None
    follow_up_date: Optional[date] = None
    notes: Optional[str] = ""
    consultation_type: Optional[str] = None
    consultation_subtype: Optional[str] = None

@router.post("/complete", response_model=Consultation)
def complete_consultation(
    req: ConsultationCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_clinical_edit())
):
    tenant_id = current_user.tenant_id
    branch_id = current_user.branch_id
    
    consultation_repo = SQLAlchemyConsultationRepository(db)
    appointment_repo = SQLAlchemyAppointmentRepository(db)
    vitals_repo = SQLAlchemyVitalsRepository(db)
    consultation_service = ConsultationService(consultation_repo, appointment_repo, vitals_repo)
    
    try:
        return consultation_service.complete_consultation(
            tenant_id=tenant_id,
            branch_id=branch_id,
            appointment_id=req.appointment_id,
            symptoms=req.symptoms,
            diagnosis=req.diagnosis,
            prescription=req.prescription,
            blood_pressure=req.blood_pressure,
            weight=req.weight,
            height=req.height,
            bmi=req.bmi,
            temperature=req.temperature,
            pulse_rate=req.pulse_rate,
            spo2=req.spo2,
            respiratory_rate=req.respiratory_rate,
            follow_up_date=req.follow_up_date,
            notes=req.notes,
            consultation_type=req.consultation_type,
            consultation_subtype=req.consultation_subtype
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/patient/{patient_id}/history", response_model=List[Consultation])
def get_patient_history(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_clinical_view())
):
    tenant_id = current_user.tenant_id
    consultation_repo = SQLAlchemyConsultationRepository(db)
    appointment_repo = SQLAlchemyAppointmentRepository(db)
    consultation_service = ConsultationService(consultation_repo, appointment_repo)
    return consultation_service.get_patient_history(patient_id, tenant_id)

@router.get("/{consultation_id}/print")
def print_prescription(
    consultation_id: str,
    lang: str = "en",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_clinical_view())
):
    tenant_id = current_user.tenant_id
    consultation_repo = SQLAlchemyConsultationRepository(db)
    patient_repo = SQLAlchemyPatientRepository(db)
    
    consultation = consultation_repo.find_by_id(consultation_id, tenant_id)
    if not consultation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")
        
    patient = patient_repo.find_by_id(consultation.patient_id, tenant_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        
    doc_gen = PDFGeneratorAdapter()
    user_repo = SQLAlchemyUserRepository(db)
    doctor = user_repo.find_by_id(consultation.doctor_id, tenant_id)
    settings_repo = SQLAlchemyClinicSettingsRepository(db)
    clinic_settings = settings_repo.get(tenant_id, current_user.branch_id)

    try:
        pdf_bytes = doc_gen.generate_prescription_pdf(consultation, patient, lang, doctor=doctor, clinic_settings=clinic_settings)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
