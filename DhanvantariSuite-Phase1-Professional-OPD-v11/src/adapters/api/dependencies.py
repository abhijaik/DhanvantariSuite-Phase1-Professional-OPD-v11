from typing import Generator, Tuple, Optional
from datetime import datetime
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from src.adapters.db.connection import get_db_session
from src.services.auth_service import SECRET_KEY, ALGORITHM
from src.domain.models.user import UserRole, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)

def get_db() -> Generator[Session, None, None]:
    with get_db_session() as session:
        yield session

def get_tenant_context(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_branch_id: Optional[str] = Header(None, alias="X-Branch-ID"),
    authorization: Optional[str] = Header(None)
) -> Tuple[str, str]:
    """
    Resolves the tenant_id and branch_id for the request.
    In local single-tenant desktop mode: defaults to 'local-clinic' and 'branch-main'.
    In cloud SaaS mode: reads headers or parses JWT.
    """
    tenant_id = x_tenant_id or "local-clinic"
    branch_id = x_branch_id or "branch-main"

    # If JWT is provided, extract tenant info from it
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            tenant_id = payload.get("tenant_id", tenant_id)
            branch_id = payload.get("branch_id", branch_id)
        except JWTError:
            pass # Fallback to header or default in case of invalid token during local debug

    return tenant_id, branch_id

def get_current_user_claims(
    token: str = Depends(oauth2_scheme),
    context: Tuple[str, str] = Depends(get_tenant_context)
) -> dict:
    """Require a valid JWT for every protected API request."""
    tenant_id, branch_id = context
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        token_tenant: str = payload.get("tenant_id")
        token_branch: str = payload.get("branch_id")
        if not user_id or not username or not role:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
        return {"user_id": user_id, "username": username, "role": role, "tenant_id": token_tenant or tenant_id, "branch_id": token_branch or branch_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

def require_role(allowed_roles: list[UserRole]):
    def role_dependency(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return user
    return role_dependency

def get_current_user(
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
) -> User:
    tenant_id = claims["tenant_id"]
    user_id = claims["user_id"]
    if user_id == "local-admin-id":
        return User(
            id="local-admin-id",
            tenant_id=tenant_id,
            branch_id=claims["branch_id"],
            username="local-admin",
            password_hash="",
            full_name="Local Administrator",
            role=UserRole.ADMIN,
            can_collect_payment=True,
            can_enter_vitals=True,
            can_view_clinical_history=True,
            can_edit_clinical_data=True,
            status="Active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    from src.adapters.db.repositories import SQLAlchemyUserRepository
    user_repo = SQLAlchemyUserRepository(db)
    user = user_repo.find_by_id(user_id, tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != "Active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is deactivated"
        )
    return user

def require_payment_collection():
    def dep(user: User = Depends(get_current_user)):
        if user.role == UserRole.ADMIN:
            return user
        if not user.can_collect_payment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to collect payments")
        return user
    return dep

def require_vitals_recording():
    def dep(user: User = Depends(get_current_user)):
        if user.role == UserRole.ADMIN:
            return user
        if not user.can_enter_vitals:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to enter vitals")
        return user
    return dep

def require_clinical_view():
    def dep(user: User = Depends(get_current_user)):
        if user.role in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.DOCTOR_ALL]:
            return user
        if not user.can_view_clinical_history:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view clinical history")
        return user
    return dep

def require_clinical_edit():
    def dep(user: User = Depends(get_current_user)):
        # Phase 1: only doctors can create/update clinical consultation data.
        if user.role in [UserRole.DOCTOR, UserRole.DOCTOR_ALL] and user.can_edit_clinical_data:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an authorized Doctor can edit clinical consultation data")
    return dep
