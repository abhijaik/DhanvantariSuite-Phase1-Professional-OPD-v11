from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from typing import Optional
from pydantic import BaseModel

from src.adapters.api.dependencies import get_db, require_role, get_current_user
from src.domain.models.user import UserRole, User
from src.domain.models.clinic_settings import ClinicSettings
from src.adapters.db.repositories import SQLAlchemyClinicSettingsRepository

router = APIRouter(prefix="/api/settings", tags=["Clinic Settings"])

class UpdateSettingsRequest(BaseModel):
    clinic_name: str
    clinic_address: str
    phone: str
    email: Optional[str] = None
    logo_url: Optional[str] = None
    license_number: Optional[str] = None
    currency: str = "INR"
    tax_enabled: bool = False
    invoice_prefix: str = "INV"
    invoice_language_default: str = "en"
    appointment_duration: int = 15
    vitals_entry_by: str = "Both"

@router.get("", response_model=ClinicSettings)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]))
):
    tenant_id = current_user.tenant_id
    branch_id = current_user.branch_id
    
    repo = SQLAlchemyClinicSettingsRepository(db)
    settings = repo.get(tenant_id, branch_id)
    if not settings:
        # Return sensible default settings if none found
        default_settings = ClinicSettings(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            clinic_name="My Local Clinic",
            clinic_address="123 Clinic Road, Suite A",
            phone="555-0199",
            email="info@localclinic.com",
            logo_url="",
            license_number="LIC-12345",
            currency="INR",
            tax_enabled=False,
            invoice_prefix="INV",
            invoice_language_default="en",
            appointment_duration=15,
            vitals_entry_by="Both",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        # Auto-save it
        repo.save(default_settings)
        return default_settings
    return settings

@router.post("", response_model=ClinicSettings)
def update_settings(
    req: UpdateSettingsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    tenant_id = current_user.tenant_id
    branch_id = current_user.branch_id
    
    repo = SQLAlchemyClinicSettingsRepository(db)
    settings = repo.get(tenant_id, branch_id)
    if not settings:
        settings = ClinicSettings(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            clinic_name=req.clinic_name,
            clinic_address=req.clinic_address,
            phone=req.phone,
            email=req.email,
            logo_url=req.logo_url,
            license_number=req.license_number,
            currency=req.currency,
            tax_enabled=req.tax_enabled,
            invoice_prefix=req.invoice_prefix,
            invoice_language_default=req.invoice_language_default,
            appointment_duration=req.appointment_duration,
            vitals_entry_by=req.vitals_entry_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    else:
        settings.clinic_name = req.clinic_name
        settings.clinic_address = req.clinic_address
        settings.phone = req.phone
        settings.email = req.email
        settings.logo_url = req.logo_url
        settings.license_number = req.license_number
        settings.currency = req.currency
        settings.tax_enabled = req.tax_enabled
        settings.invoice_prefix = req.invoice_prefix
        settings.invoice_language_default = req.invoice_language_default
        settings.appointment_duration = req.appointment_duration
        settings.vitals_entry_by = req.vitals_entry_by
        settings.updated_at = datetime.utcnow()
        
    repo.save(settings)
    return settings
