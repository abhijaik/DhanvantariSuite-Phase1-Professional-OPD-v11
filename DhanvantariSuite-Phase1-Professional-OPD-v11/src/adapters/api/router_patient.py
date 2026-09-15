from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional

from src.adapters.api.dependencies import get_db, get_current_user, require_role
from src.adapters.db.repositories import SQLAlchemyPatientRepository, SQLAlchemyUserRepository, SQLAlchemyAppointmentRepository
from src.services.patient_service import PatientService
from src.services.queue_service import QueueService
from src.domain.models.user import UserRole, User
from src.domain.models.patient import Patient

router = APIRouter(prefix="/api/patients", tags=["Patients"])


def active_doctors(db: Session, current_user: User):
    return [u for u in SQLAlchemyUserRepository(db).list_by_branch(current_user.tenant_id, current_user.branch_id)
            if u.role == UserRole.DOCTOR and u.status == "Active"]


def resolve_doctor_id(db: Session, current_user: User, requested_doctor_id: Optional[str]) -> str:
    doctors = active_doctors(db, current_user)
    if current_user.role == UserRole.DOCTOR:
        return current_user.id
    if requested_doctor_id:
        if any(d.id == requested_doctor_id for d in doctors):
            return requested_doctor_id
        raise HTTPException(status_code=400, detail="Selected doctor is not active in this clinic.")
    if len(doctors) == 1:
        return doctors[0].id
    if not doctors:
        raise HTTPException(status_code=400, detail="No active doctor is configured for this clinic.")
    raise HTTPException(status_code=400, detail="Please select a doctor for this visit.")


def is_multi_doctor(db: Session, current_user: User) -> bool:
    return len(active_doctors(db, current_user)) > 1


class PatientRegisterRequest(BaseModel):
    full_name: str
    mobile: str
    date_of_birth: date
    age: int
    gender: str
    address: Optional[str] = ""
    registration_date: Optional[date] = None
    alternate_number: Optional[str] = None
    email: Optional[str] = None
    blood_group: Optional[str] = None
    marital_status: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[str] = ""
    medical_notes: Optional[str] = ""
    referred_by: Optional[str] = None


class RegisterPatientAndVisitRequest(PatientRegisterRequest):
    doctor_id: Optional[str] = None
    visit_type: str = "New Patient"
    consultation_type: str = "General Consultation"
    consultation_subtype: Optional[str] = None
    notes: Optional[str] = ""
    referred_by_type: Optional[str] = None
    referred_by_name: Optional[str] = None
    check_in_now: bool = True


class StartExistingVisitRequest(BaseModel):
    doctor_id: Optional[str] = None
    visit_type: str = "Follow-Up"
    consultation_type: str = "General Consultation"
    consultation_subtype: Optional[str] = None
    notes: Optional[str] = ""
    referred_by_type: Optional[str] = None
    referred_by_name: Optional[str] = None
    check_in_now: bool = True


@router.post("/register", response_model=Patient)
def register_patient(
    req: PatientRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]))
):
    patient_service = PatientService(SQLAlchemyPatientRepository(db))
    try:
        return patient_service.register_patient(
            tenant_id=current_user.tenant_id,
            branch_id=current_user.branch_id,
            full_name=req.full_name,
            mobile=req.mobile,
            date_of_birth=req.date_of_birth,
            age=req.age,
            gender=req.gender,
            address=req.address or "",
            registration_date=req.registration_date,
            alternate_number=req.alternate_number,
            email=req.email,
            blood_group=req.blood_group,
            marital_status=req.marital_status,
            emergency_contact=req.emergency_contact,
            allergies=req.allergies,
            medical_notes=req.medical_notes,
            referred_by=req.referred_by
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/register-visit")
def register_patient_and_visit(
    req: RegisterPatientAndVisitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]))
):
    tenant_id, branch_id = current_user.tenant_id, current_user.branch_id
    doctors = active_doctors(db, current_user)
    multi = len(doctors) > 1
    doctor_id = resolve_doctor_id(db, current_user, req.doctor_id)

    # Prevent creating a second patient when a matching mobile already exists.
    normalized = Patient.normalize_mobile(req.mobile)
    existing = SQLAlchemyPatientRepository(db).find_by_mobile(normalized, tenant_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Patient already exists as {existing.patient_number}. Search the patient and start a new visit instead.")

    patient_service = PatientService(SQLAlchemyPatientRepository(db))
    try:
        patient = patient_service.register_patient(
            tenant_id=tenant_id, branch_id=branch_id, full_name=req.full_name, mobile=req.mobile,
            date_of_birth=req.date_of_birth, age=req.age, gender=req.gender, address=req.address or "",
            alternate_number=req.alternate_number, email=req.email, blood_group=req.blood_group,
            marital_status=req.marital_status, emergency_contact=req.emergency_contact,
            allergies=req.allergies, medical_notes=req.medical_notes, referred_by=req.referred_by
        )
        appt = QueueService(SQLAlchemyAppointmentRepository(db)).book_appointment(
            tenant_id=tenant_id, branch_id=branch_id, patient_id=patient.id, doctor_id=doctor_id,
            appointment_date=date.today(), scheduled_time=datetime.now().time(), visit_type=req.visit_type,
            consultation_type=req.consultation_type, consultation_subtype=req.consultation_subtype, notes=req.notes,
            referred_by_type=req.referred_by_type, referred_by_name=req.referred_by_name
        )
        repo = SQLAlchemyAppointmentRepository(db)
        doctor_self_start = current_user.role == UserRole.DOCTOR
        if multi and not doctor_self_start:
            token_num = repo.get_next_token_value(date.today(), doctor_id, tenant_id, branch_id)
            appt.queue_token = f"T-{token_num:02d}"
        if req.check_in_now:
            if doctor_self_start:
                appt.status = appt.status.__class__.CONSULTING
            elif multi:
                appt.status = appt.status.__class__.IN_QUEUE
            else:
                # Single-doctor clinics do not need a token. Reception marks arrival;
                # the doctor opens the visit from Today.
                appt.status = appt.status.__class__.BOOKED
        repo.save(appt)
        return {"patient": patient, "appointment": appt, "multi_doctor": multi, "doctor_id": doctor_id}
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{patient_id}/start-visit")
def start_visit_for_existing_patient(
    patient_id: str,
    req: StartExistingVisitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]))
):
    tenant_id, branch_id = current_user.tenant_id, current_user.branch_id
    patient = SQLAlchemyPatientRepository(db).find_by_id(patient_id, tenant_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    doctor_id = resolve_doctor_id(db, current_user, req.doctor_id)
    multi = is_multi_doctor(db, current_user)
    repo = SQLAlchemyAppointmentRepository(db)
    appt = QueueService(repo).book_appointment(
        tenant_id=tenant_id, branch_id=branch_id, patient_id=patient.id, doctor_id=doctor_id,
        appointment_date=date.today(), scheduled_time=datetime.now().time(), visit_type=req.visit_type,
        consultation_type=req.consultation_type, consultation_subtype=req.consultation_subtype, notes=req.notes,
        referred_by_type=req.referred_by_type, referred_by_name=req.referred_by_name
    )
    doctor_self_start = current_user.role == UserRole.DOCTOR
    if multi and not doctor_self_start:
        token_num = repo.get_next_token_value(date.today(), doctor_id, tenant_id, branch_id)
        appt.queue_token = f"T-{token_num:02d}"
        if req.check_in_now:
            appt.status = appt.status.__class__.IN_QUEUE
    elif req.check_in_now:
        appt.status = appt.status.__class__.CONSULTING if doctor_self_start else appt.status.__class__.BOOKED
    repo.save(appt)
    return {"patient": patient, "appointment": appt, "multi_doctor": multi, "doctor_id": doctor_id}


@router.get("/search", response_model=List[Patient])
def search_patients(q: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return PatientService(SQLAlchemyPatientRepository(db)).search_patients(q, current_user.tenant_id)


@router.get("/{patient_id}", response_model=Patient)
def get_patient(patient_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = SQLAlchemyPatientRepository(db).find_by_id(patient_id, current_user.tenant_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
