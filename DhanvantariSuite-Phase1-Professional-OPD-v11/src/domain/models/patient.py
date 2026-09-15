import re
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator, ConfigDict

class Patient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    patient_number: str
    registration_date: date
    full_name: str
    date_of_birth: date
    age: int
    gender: str
    mobile_normalized: str
    alternate_number: Optional[str] = None
    email: Optional[str] = None
    address: str
    blood_group: Optional[str] = None
    marital_status: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[str] = ""
    medical_notes: Optional[str] = ""
    referred_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def normalize_mobile(mobile: str) -> str:
        # Strip all non-digit characters except leading plus
        cleaned = re.sub(r'(?<!^\+)[^\d]', '', mobile.strip())
        # Clean anything else non-numeric
        cleaned = re.sub(r'[^\d+]', '', cleaned)
        # Ensure default Indian prefix if 10 digits without prefix
        if len(cleaned) == 10 and not cleaned.startswith('+'):
            cleaned = "+91" + cleaned
        elif len(cleaned) == 12 and cleaned.startswith('91') and not cleaned.startswith('+'):
            cleaned = "+" + cleaned
        return cleaned
