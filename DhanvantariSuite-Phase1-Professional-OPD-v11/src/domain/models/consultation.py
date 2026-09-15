from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class PrescriptionItem(BaseModel):
    medicine_name: str
    dosage: str          # e.g., "1-0-1" or "1 tab"
    frequency: str       # e.g., "Once daily", "Twice daily"
    duration: str        # e.g., "5 days"
    food_relation: Optional[str] = "After Food"
    instructions: Optional[str] = ""

class Consultation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    appointment_id: str
    patient_id: str
    doctor_id: str
    consultation_type: Optional[str] = None
    consultation_subtype: Optional[str] = None
    symptoms: List[str]            # Structured list
    diagnosis: str
    prescription: List[PrescriptionItem] # Structured prescription list
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
    created_at: datetime
    updated_at: datetime
