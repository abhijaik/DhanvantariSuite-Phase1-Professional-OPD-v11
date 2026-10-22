from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AuditLog(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    user_id: str
    user_role: Optional[str] = None
    action: str
    module: str
    record_id: str
    ip_address: Optional[str] = None
    timestamp: datetime
    summary: str
