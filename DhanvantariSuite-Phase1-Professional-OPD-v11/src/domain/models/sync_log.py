from enum import Enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SyncOperation(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class SyncLog(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    table_name: str
    record_id: str
    operation: SyncOperation
    payload: str            # Serialized JSON string of the record data
    timestamp: datetime
    synced: bool
