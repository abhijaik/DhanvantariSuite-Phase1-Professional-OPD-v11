from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    DOCTOR_ALL = "DOCTOR_ALL"
    RECEPTIONIST = "RECEPTIONIST"
    SUPERDOC = "SUPERDOC"  # legacy database compatibility only; never assign in Phase 1 UI/API

class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    username: str
    password_hash: str
    full_name: str
    role: UserRole
    mobile: Optional[str] = None
    can_collect_payment: bool = True
    can_enter_vitals: bool = True
    can_view_clinical_history: bool = True
    can_edit_clinical_data: bool = True
    status: str = "Active"
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
