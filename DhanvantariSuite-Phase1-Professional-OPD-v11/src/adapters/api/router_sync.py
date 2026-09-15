from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from src.adapters.api.dependencies import get_db, require_role
from src.adapters.db.repositories import SQLAlchemySyncLogRepository
from src.domain.models.user import UserRole, User
from src.domain.models.sync_log import SyncLog

router = APIRouter(prefix="/api/sync", tags=["Sync Engine"])

class SyncAckRequest(BaseModel):
    log_ids: List[str]

@router.get("/unsynced", response_model=List[SyncLog])
def get_unsynced_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    tenant_id = current_user.tenant_id
    sync_repo = SQLAlchemySyncLogRepository(db)
    return sync_repo.get_unsynced(tenant_id, limit)

@router.post("/ack")
def acknowledge_sync(
    req: SyncAckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    tenant_id = current_user.tenant_id
    sync_repo = SQLAlchemySyncLogRepository(db)
    sync_repo.mark_as_synced(req.log_ids, tenant_id)
    return {"status": "success", "message": f"Acknowledged {len(req.log_ids)} transaction logs"}
