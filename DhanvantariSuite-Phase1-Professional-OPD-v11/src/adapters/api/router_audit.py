from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.domain.models.audit_log import AuditLog
from src.domain.models.user import User, UserRole
from src.services.audit_service import AuditService
from src.adapters.api.dependencies import get_db, get_current_user, require_role, get_tenant_context

router = APIRouter(prefix="/api/audit-logs", tags=["Audit & Compliance"])

@router.get("", response_model=List[AuditLog])
def get_audit_logs(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    module: Optional[str] = Query(None, description="Module filter, e.g. PATIENT, CONSULTATION, AUTH"),
    action: Optional[str] = Query(None, description="Action filter, e.g. READ_PATIENT, PRINT_PRESCRIPTION"),
    target_user_id: Optional[str] = Query(None, description="Filter by user id"),
    branch_id: Optional[str] = Query(None, description="Filter by branch id"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db),
    tenant_context: tuple[str, str] = Depends(get_tenant_context)
):
    """
    HIPAA § 164.312(b) & DPDP Act 2023 Audit Log Retrieval Endpoint.
    Restricted strictly to system Administrators.
    """
    tenant_id, _ = tenant_context
    
    audit_service = AuditService(db)
    return audit_service.query(
        tenant_id=tenant_id,
        branch_id=branch_id,
        from_date=from_date,
        to_date=to_date,
        module=module,
        action=action,
        user_id=target_user_id,
        limit=limit,
        offset=offset
    )
