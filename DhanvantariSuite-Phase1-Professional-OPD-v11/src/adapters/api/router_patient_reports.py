import os
import re
import uuid
import mimetypes
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.adapters.api.dependencies import get_db, require_role, get_current_user, get_tenant_context
from src.domain.models.user import User, UserRole
from src.domain.models.patient_report import PatientReport
from src.adapters.db.orm_models import PatientReportORM, PatientORM
from src.services.audit_service import AuditService

router = APIRouter(prefix="/api/patient-reports", tags=["Patient Reports"])

UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads" / "reports"
ALLOWED_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp",
    ".docx", ".doc", ".txt", ".csv", ".xlsx"
}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


class ReportLinkRequest(BaseModel):
    patient_id: str
    report_title: str
    report_type: str
    report_date: Optional[date] = None
    source_type: str = "GOOGLE_DRIVE"  # GOOGLE_DRIVE or EXTERNAL_URL
    external_url: str
    notes: Optional[str] = ""


def _extract_google_drive_preview(url: str) -> Optional[str]:
    match = re.search(r'(?:/d/|id=)([a-zA-Z0-9_-]{25,})', url)
    if match:
        return f"https://drive.google.com/file/d/{match.group(1)}/preview"
    return None


@router.post("/upload-file", response_model=PatientReport)
async def upload_patient_report_file(
    request: Request,
    patient_id: str = Form(...),
    report_title: str = Form(...),
    report_type: str = Form(...),
    report_date: Optional[date] = Form(None),
    source_type: str = Form("FILE_UPLOAD"),
    notes: Optional[str] = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL, UserRole.RECEPTIONIST])),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """Upload a diagnostic or lab report file (PDF, Image, Scan) for a patient."""
    tenant_id, branch_id = tenant_context
    client_ip = request.client.host if request.client else None

    patient = db.query(PatientORM).filter(
        PatientORM.id == patient_id,
        PatientORM.tenant_id == tenant_id
    ).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    orig_name = file.filename or "report.pdf"
    ext = Path(orig_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Read content and check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of 25MB (size: {len(content) / (1024*1024):.1f}MB)."
        )

    report_id = str(uuid.uuid4())
    safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', orig_name)
    target_dir = UPLOAD_ROOT / tenant_id / patient_id
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{report_id[:8]}_{safe_name}"
    target_file = target_dir / stored_filename

    with open(target_file, "wb") as f:
        f.write(content)

    mime = file.content_type or mimetypes.guess_type(orig_name)[0] or "application/octet-stream"
    rel_path = str(Path(tenant_id) / patient_id / stored_filename)
    eff_date = report_date or date.today()
    valid_source = source_type if source_type in ["FILE_UPLOAD", "CAMERA_SCAN"] else "FILE_UPLOAD"

    report_orm = PatientReportORM(
        id=report_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        patient_id=patient_id,
        uploaded_by_id=current_user.id,
        uploaded_by_name=current_user.full_name,
        report_title=report_title.strip() or orig_name,
        report_type=report_type.strip() or "General Lab",
        report_date=eff_date,
        source_type=valid_source,
        file_path=rel_path,
        file_name=orig_name,
        file_size_bytes=len(content),
        mime_type=mime,
        external_url=None,
        notes=notes.strip() if notes else "",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(report_orm)
    db.commit()
    db.refresh(report_orm)

    AuditService(db).record(
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        action="UPLOAD_PATIENT_REPORT",
        module="REPORTS",
        record_id=report_id,
        summary=f"Uploaded report '{report_title}' ({orig_name}, {valid_source}) for patient {patient.full_name}",
        ip_address=client_ip
    )

    return report_orm


@router.post("/link", response_model=PatientReport)
def add_patient_report_link(
    request: Request,
    req: ReportLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL, UserRole.RECEPTIONIST])),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """Attach an external Google Drive link or Cloud Document URL to patient history."""
    tenant_id, branch_id = tenant_context
    client_ip = request.client.host if request.client else None

    patient = db.query(PatientORM).filter(
        PatientORM.id == req.patient_id,
        PatientORM.tenant_id == tenant_id
    ).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    raw_url = (req.external_url or "").strip()
    if not re.match(r'^https?://', raw_url, re.IGNORECASE):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid HTTP or HTTPS URL is required.")

    source_type = req.source_type
    if "drive.google.com" in raw_url.lower():
        source_type = "GOOGLE_DRIVE"

    report_id = str(uuid.uuid4())
    eff_date = req.report_date or date.today()

    report_orm = PatientReportORM(
        id=report_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        patient_id=req.patient_id,
        uploaded_by_id=current_user.id,
        uploaded_by_name=current_user.full_name,
        report_title=req.report_title.strip() or "Diagnostic Report",
        report_type=req.report_type.strip() or "Other",
        report_date=eff_date,
        source_type=source_type,
        file_path=None,
        file_name=None,
        file_size_bytes=None,
        mime_type="text/html",
        external_url=raw_url,
        notes=req.notes.strip() if req.notes else "",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(report_orm)
    db.commit()
    db.refresh(report_orm)

    AuditService(db).record(
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        action="UPLOAD_PATIENT_REPORT",
        module="REPORTS",
        record_id=report_id,
        summary=f"Linked {source_type} report '{req.report_title}' for patient {patient.full_name}",
        ip_address=client_ip
    )

    return report_orm


@router.get("/patient/{patient_id}", response_model=List[PatientReport])
def list_patient_reports(
    patient_id: str,
    request: Request,
    report_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL, UserRole.RECEPTIONIST])),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """Retrieve all diagnostic and lab reports for a patient."""
    tenant_id, branch_id = tenant_context
    client_ip = request.client.host if request.client else None

    query = db.query(PatientReportORM).filter(
        PatientReportORM.patient_id == patient_id,
        PatientReportORM.tenant_id == tenant_id
    )
    if report_type:
        query = query.filter(PatientReportORM.report_type == report_type)

    reports = query.order_by(PatientReportORM.report_date.desc(), PatientReportORM.created_at.desc()).all()

    AuditService(db).record(
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        action="READ_PATIENT_REPORTS",
        module="REPORTS",
        record_id=patient_id,
        summary=f"Viewed {len(reports)} report(s) for patient {patient_id}",
        ip_address=client_ip
    )

    return reports


@router.get("/{report_id}/file")
def get_report_file(
    report_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL, UserRole.RECEPTIONIST])),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """Download or view the raw report file."""
    tenant_id, branch_id = tenant_context
    client_ip = request.client.host if request.client else None

    report = db.query(PatientReportORM).filter(
        PatientReportORM.id == report_id,
        PatientReportORM.tenant_id == tenant_id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if not report.file_path:
        if report.external_url:
            return {"external_url": report.external_url}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No local file associated with this report.")

    abs_path = (UPLOAD_ROOT / report.file_path).resolve()
    # Path traversal check
    if not str(abs_path).startswith(str(UPLOAD_ROOT.resolve())):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    if not abs_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found on disk.")

    AuditService(db).record(
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        action="VIEW_PATIENT_REPORT",
        module="REPORTS",
        record_id=report_id,
        summary=f"Downloaded/Viewed report file '{report.report_title}' ({report.file_name})",
        ip_address=client_ip
    )

    return FileResponse(
        path=abs_path,
        media_type=report.mime_type or "application/octet-stream",
        filename=report.file_name or "report"
    )


@router.delete("/{report_id}")
def delete_patient_report(
    report_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL])),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """Delete a patient report record and its file."""
    tenant_id, branch_id = tenant_context
    client_ip = request.client.host if request.client else None

    report = db.query(PatientReportORM).filter(
        PatientReportORM.id == report_id,
        PatientReportORM.tenant_id == tenant_id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    # Remove file from disk if local
    if report.file_path:
        try:
            abs_path = (UPLOAD_ROOT / report.file_path).resolve()
            if abs_path.exists() and str(abs_path).startswith(str(UPLOAD_ROOT.resolve())):
                abs_path.unlink(missing_ok=True)
        except Exception:
            pass

    title = report.report_title
    patient_id = report.patient_id
    db.delete(report)
    db.commit()

    AuditService(db).record(
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        action="DELETE_PATIENT_REPORT",
        module="REPORTS",
        record_id=report_id,
        summary=f"Deleted report '{title}' for patient {patient_id}",
        ip_address=client_ip
    )

    return {"status": "deleted", "id": report_id}
