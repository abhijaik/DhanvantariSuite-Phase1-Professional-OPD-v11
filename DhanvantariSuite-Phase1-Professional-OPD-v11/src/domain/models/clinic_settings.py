from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ClinicSettings(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
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
    vitals_entry_by: str = "Both" # "Doctor", "Receptionist", or "Both"
    created_at: datetime
    updated_at: datetime
