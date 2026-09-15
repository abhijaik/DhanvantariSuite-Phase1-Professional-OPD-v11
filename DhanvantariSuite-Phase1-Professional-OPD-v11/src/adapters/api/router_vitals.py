from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from src.adapters.api.dependencies import get_db, get_current_user, require_role, require_vitals_recording
from src.domain.models.user import UserRole, User
from src.adapters.db.repositories import SQLAlchemyVitalsRepository, SQLAlchemyVitalsConfigRepository
from src.services.vitals_service import VitalsService

router = APIRouter(prefix="/api/vitals", tags=["vitals"])

def get_vitals_service(session: Session = Depends(get_db)) -> VitalsService:
    vitals_repo = SQLAlchemyVitalsRepository(session)
    config_repo = SQLAlchemyVitalsConfigRepository(session)
    return VitalsService(vitals_repo, config_repo)

class VitalsConfigRequest(BaseModel):
    recorder_role: str # RECEPTIONIST, NURSE, DOCTOR, ANY

class RecordVitalsRequest(BaseModel):
    appointment_id: str
    blood_pressure: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    temperature: Optional[float] = None
    pulse: Optional[int] = None
    spo2: Optional[int] = None
    respiratory_rate: Optional[int] = None

@router.get("/config")
def get_vitals_config(
    current_user: User = Depends(get_current_user),
    service: VitalsService = Depends(get_vitals_service)
):
    role = service.get_recorder_role(current_user.tenant_id, current_user.branch_id)
    return {"recorder_role": role}

@router.post("/config")
def update_vitals_config(
    req: VitalsConfigRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    service: VitalsService = Depends(get_vitals_service)
):
    if req.recorder_role not in ["Receptionist", "Doctor", "Both"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid recorder role. Allowed: Receptionist, Doctor, Both"
        )
    service.set_recorder_role(current_user.tenant_id, current_user.branch_id, req.recorder_role)
    return {"status": "success", "recorder_role": req.recorder_role}

@router.post("/record")
def record_vitals(
    req: RecordVitalsRequest,
    current_user: User = Depends(require_vitals_recording()),
    service: VitalsService = Depends(get_vitals_service)
):
    current_role = current_user.role.value
    allowed_role = service.get_recorder_role(current_user.tenant_id, current_user.branch_id)

    # If role config is set to a specific role, restrict logging
    # SuperDoc/Admin bypasses this
    if current_role not in [UserRole.ADMIN.value] and allowed_role not in ["Both", "ANY"]:
        if allowed_role == "Doctor" and current_role != UserRole.DOCTOR.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Doctors are permitted to record vitals according to clinic settings."
            )
        if allowed_role == "Receptionist" and current_role != UserRole.RECEPTIONIST.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Receptionists are permitted to record vitals according to clinic settings."
            )

    recorder_name_and_role = f"{current_user.username} ({current_role})"
    vitals = service.record_vitals(
        tenant_id=current_user.tenant_id,
        branch_id=current_user.branch_id,
        appointment_id=req.appointment_id,
        blood_pressure=req.blood_pressure,
        weight=req.weight,
        height=req.height,
        temperature=req.temperature,
        pulse=req.pulse,
        spo2=req.spo2,
        respiratory_rate=req.respiratory_rate,
        recorded_by=recorder_name_and_role
    )
    return vitals

@router.get("/appointment/{appointment_id}")
def get_vitals(
    appointment_id: str,
    current_user: User = Depends(get_current_user),
    service: VitalsService = Depends(get_vitals_service)
):
    vitals = service.get_vitals_by_appointment(appointment_id, current_user.tenant_id)
    if not vitals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vitals not found for this appointment"
        )
    return vitals
