from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AuditLog(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    user_id: str
    action: str
    module: str
    record_id: str
    timestamp: datetime
    summary: str
