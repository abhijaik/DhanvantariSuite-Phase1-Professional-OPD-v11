import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.adapters.api.dependencies import get_db, require_role, get_tenant_context
from src.domain.models.user import User, UserRole
from src.services.backup_service import BackupService, BACKUP_ROOT
from src.services.audit_service import AuditService

router = APIRouter(prefix="/api/backup", tags=["Database Backup & Restore"])


@router.post("/create")
def create_backup(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL])),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """Create an instant complete clinic backup archive (.dhanbackup)."""
    tenant_id, branch_id = tenant_context
    client_ip = request.client.host if request.client else None

    service = BackupService(db)
    result = service.create_backup(
        tenant_id=tenant_id,
        branch_id=branch_id,
        backup_type="MANUAL",
        created_by_user_id=current_user.id
    )

    AuditService(db).record(
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        action="CREATE_DATABASE_BACKUP",
        module="SYSTEM",
        record_id=result["filename"],
        summary=f"Created database backup '{result['filename']}' ({result['file_size_bytes']} bytes)",
        ip_address=client_ip
    )

    return result


@router.get("/list")
def list_backups(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL])),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """List all available backup archives for this tenant."""
    tenant_id, _ = tenant_context
    service = BackupService(db)
    return service.list_backups(tenant_id)


@router.get("/download/{filename}")
def download_backup_file(
    filename: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL])),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """Download a specific .dhanbackup file."""
    tenant_id, branch_id = tenant_context
    client_ip = request.client.host if request.client else None

    # Sanitize filename
    safe_filename = Path(filename).name
    file_path = (BACKUP_ROOT / tenant_id / safe_filename).resolve()

    if not file_path.exists() or not str(file_path).startswith(str((BACKUP_ROOT / tenant_id).resolve())):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found.")

    AuditService(db).record(
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        action="DOWNLOAD_DATABASE_BACKUP",
        module="SYSTEM",
        record_id=safe_filename,
        summary=f"Downloaded backup archive '{safe_filename}'",
        ip_address=client_ip
    )

    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=safe_filename
    )


@router.post("/restore")
async def restore_from_backup(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL])),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """Restore database and files from an uploaded .dhanbackup file."""
    tenant_id, branch_id = tenant_context
    client_ip = request.client.host if request.client else None

    if not file.filename.endswith(".dhanbackup") and not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup file type. Expected .dhanbackup file."
        )

    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dhanbackup") as tmp:
        tmp_path = Path(tmp.name)
        content = await file.read()
        tmp.write(content)

    try:
        service = BackupService(db)
        result = service.restore_backup(tenant_id=tenant_id, archive_path=tmp_path)

        AuditService(db).record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=current_user.id,
            user_role=current_user.role.value,
            action="RESTORE_DATABASE_BACKUP",
            module="SYSTEM",
            record_id=file.filename,
            summary=f"Restored database from backup file '{file.filename}'",
            ip_address=client_ip
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Restore failed: {str(e)}")
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


@router.post("/auto-check")
def run_auto_backup_check(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL, UserRole.RECEPTIONIST])),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """Checks if daily automatic backup is due (> 24 hours) and creates it."""
    tenant_id, branch_id = tenant_context
    service = BackupService(db)
    result = service.check_and_run_auto_backup(tenant_id, branch_id)
    if result:
        AuditService(db).record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=current_user.id,
            user_role=current_user.role.value,
            action="AUTO_DATABASE_BACKUP",
            module="SYSTEM",
            record_id=result["filename"],
            summary=f"Automatic daily backup created '{result['filename']}'",
            ip_address=request.client.host if request.client else None
        )
    return {"auto_backup_created": bool(result), "details": result}
