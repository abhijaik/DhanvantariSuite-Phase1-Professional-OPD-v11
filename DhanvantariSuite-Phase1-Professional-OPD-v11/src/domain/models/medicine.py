from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class Medicine(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    generic_name: Optional[str] = None
    dosage_form: Optional[str] = "Tablet"
    default_timing: Optional[str] = "1-0-1"
    default_duration: Optional[str] = "5 Days"
    default_food_relation: Optional[str] = "After Food"
    instructions: Optional[str] = ""
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
