from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, time, datetime
from typing import List, Optional

from src.adapters.api.dependencies import get_db, get_current_user, require_role
from src.adapters.db.repositories import SQLAlchemyAppointmentRepository, SQLAlchemyPatientRepository, SQLAlchemyUserRepository
from src.services.queue_service import QueueService
from src.domain.models.user import UserRole, User
from src.domain.models.appointment import Appointment, AppointmentStatus

router = APIRouter(prefix="/api/queue", tags=["Queue & Appointments"])


def active_doctors(db, user):
    return [u for u in SQLAlchemyUserRepository(db).list_by_branch(user.tenant_id, user.branch_id)
            if u.role in [UserRole.DOCTOR, UserRole.DOCTOR_ALL] and u.status == "Active"]


class BookAppointmentRequest(BaseModel):
    patient_id: str
    doctor_id: Optional[str] = None
    appointment_date: date
    scheduled_time: time
    visit_type: str
    consultation_type: str
    notes: Optional[str] = ""
    consultation_subtype: Optional[str] = None
    referred_by_type: Optional[str] = None
    referred_by_name: Optional[str] = None
    check_in_now: bool = False


@router.get("/booked-slots")
def get_booked_slots(
    appointment_date: date,
    doctor_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenant_id, branch_id = current_user.tenant_id, current_user.branch_id
    repo = SQLAlchemyAppointmentRepository(db)
    if doctor_id:
        appts = repo.list_by_date_and_doctor(appointment_date, doctor_id, tenant_id, branch_id)
    else:
        appts = repo.list_queue(appointment_date, tenant_id, branch_id)

    booked = []
    for a in appts:
        if a.status != AppointmentStatus.CANCELLED and a.scheduled_time:
            booked.append(a.scheduled_time.strftime("%H:%M"))
    return {"booked_slots": booked}


@router.post("/book", response_model=Appointment)
def book_appointment(req: BookAppointmentRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL, UserRole.RECEPTIONIST]))):
    if req.appointment_date < date.today():
        raise HTTPException(status_code=400, detail="Cannot book appointment for a past date.")

    doctors = active_doctors(db, current_user)
    if current_user.role == UserRole.DOCTOR:
        doctor_id = current_user.id
    elif req.doctor_id and any(d.id == req.doctor_id for d in doctors):
        doctor_id = req.doctor_id
    elif len(doctors) == 1:
        doctor_id = doctors[0].id
    elif len(doctors) > 1:
        raise HTTPException(status_code=400, detail="Please select a doctor for this appointment.")
    else:
        raise HTTPException(status_code=400, detail="No active doctor is configured for this clinic.")

    repo = SQLAlchemyAppointmentRepository(db)
    appt = QueueService(repo).book_appointment(
        tenant_id=current_user.tenant_id, branch_id=current_user.branch_id, patient_id=req.patient_id,
        doctor_id=doctor_id, appointment_date=req.appointment_date, scheduled_time=req.scheduled_time,
        visit_type=req.visit_type, consultation_type=req.consultation_type, notes=req.notes,
        consultation_subtype=req.consultation_subtype,
        referred_by_type=req.referred_by_type,
        referred_by_name=req.referred_by_name
    )
    if len(doctors) > 1:
        token_num = repo.get_next_token_value(req.appointment_date, doctor_id, current_user.tenant_id, current_user.branch_id)
        appt.queue_token = f"T-{token_num:02d}"
    if req.check_in_now:
        appt.status = AppointmentStatus.IN_QUEUE if len(doctors) > 1 else AppointmentStatus.CONSULTING
    repo.save(appt)
    return appt


@router.post("/{appointment_id}/checkin", response_model=Appointment)
def check_in(appointment_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.RECEPTIONIST]))):
    appt = SQLAlchemyAppointmentRepository(db).find_by_id(appointment_id, current_user.tenant_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.status in [AppointmentStatus.IN_QUEUE, AppointmentStatus.CHECKED_IN]:
        return appt
    if appt.status not in [AppointmentStatus.SCHEDULED, AppointmentStatus.BOOKED]:
        raise HTTPException(status_code=400, detail=f"Cannot check in appointment with status {appt.status.value}")
    doctors = active_doctors(db, current_user)
    if len(doctors) == 1:
        appt.status = AppointmentStatus.CHECKED_IN
        appt.updated_at = datetime.utcnow()
        return SQLAlchemyAppointmentRepository(db).save(appt)
    return QueueService(SQLAlchemyAppointmentRepository(db)).check_in_patient(appointment_id, current_user.tenant_id)


@router.post("/{appointment_id}/start-consult", response_model=Appointment)
def start_consult(appointment_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role([UserRole.DOCTOR, UserRole.DOCTOR_ALL]))):
    repo = SQLAlchemyAppointmentRepository(db)
    appt = repo.find_by_id(appointment_id, current_user.tenant_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if current_user.role == UserRole.DOCTOR and appt.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="This patient is assigned to another doctor.")
    if appt.status == AppointmentStatus.CONSULTING:
        return appt
    doctors = active_doctors(db, current_user)
    if len(doctors) == 1 and appt.status in [AppointmentStatus.BOOKED, AppointmentStatus.CHECKED_IN]:
        appt.status = AppointmentStatus.CONSULTING
        repo.save(appt)
        return appt
    if appt.status != AppointmentStatus.IN_QUEUE:
        raise HTTPException(status_code=400, detail="Patient must be checked in before consultation starts.")
    return QueueService(repo).start_consultation(appointment_id, current_user.tenant_id)


@router.get("/live", response_model=List[Appointment])
def get_live_queue(query_date: Optional[date] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue = QueueService(SQLAlchemyAppointmentRepository(db)).get_live_queue(current_user.tenant_id, current_user.branch_id, query_date)
    if current_user.role == UserRole.DOCTOR:
        queue = [a for a in queue if a.doctor_id == current_user.id]
    return queue


@router.get("/live/details")
def get_live_queue_details(query_date: Optional[date] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue = QueueService(SQLAlchemyAppointmentRepository(db)).get_live_queue(current_user.tenant_id, current_user.branch_id, query_date)
    if current_user.role == UserRole.DOCTOR:
        queue = [a for a in queue if a.doctor_id == current_user.id]
    patient_repo = SQLAlchemyPatientRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    result = []
    for a in queue:
        p = patient_repo.find_by_id(a.patient_id, current_user.tenant_id)
        d = user_repo.find_by_id(a.doctor_id, current_user.tenant_id)
        result.append({"appointment": a, "patient": p, "doctor_name": d.full_name if d else ""})
    return result
