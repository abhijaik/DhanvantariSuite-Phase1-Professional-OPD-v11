from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class PatientVitals(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    appointment_id: str
    blood_pressure: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    bmi: Optional[float] = None
    temperature: Optional[float] = None
    pulse: Optional[int] = None
    spo2: Optional[int] = None
    respiratory_rate: Optional[int] = None
    recorded_by: str
    recorded_at: datetime
