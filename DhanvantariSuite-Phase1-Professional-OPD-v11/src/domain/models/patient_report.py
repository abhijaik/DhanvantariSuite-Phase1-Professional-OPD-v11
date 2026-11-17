from enum import Enum
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ReportSourceType(str, Enum):
    FILE_UPLOAD = "FILE_UPLOAD"
    GOOGLE_DRIVE = "GOOGLE_DRIVE"
    EXTERNAL_URL = "EXTERNAL_URL"
    CAMERA_SCAN = "CAMERA_SCAN"


class PatientReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    patient_id: str
    uploaded_by_id: str
    uploaded_by_name: str
    report_title: str
    report_type: str
    report_date: date
    source_type: str
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    external_url: Optional[str] = None
    notes: Optional[str] = ""
    created_at: datetime
    updated_at: datetime
