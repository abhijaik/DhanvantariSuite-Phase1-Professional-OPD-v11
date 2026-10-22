from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from src.adapters.api.dependencies import get_db, get_tenant_context, require_role
from src.adapters.db.repositories import SQLAlchemyUserRepository
from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.domain.models.user import UserRole, User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class UserPublic(BaseModel):
    id: str
    tenant_id: str
    branch_id: str
    username: str
    full_name: str
    role: UserRole
    mobile: Optional[str] = None
    can_collect_payment: bool = True
    can_enter_vitals: bool = True
    can_view_clinical_history: bool = False
    can_edit_clinical_data: bool = True
    status: str = "Active"
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role: UserRole
    mobile: Optional[str] = None
    can_collect_payment: bool = True
    can_enter_vitals: bool = True
    can_view_clinical_history: bool = False
    can_edit_clinical_data: bool = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    full_name: str
    can_collect_payment: bool
    can_enter_vitals: bool
    can_view_clinical_history: bool
    can_edit_clinical_data: bool
    user_id: str

@router.post("/register", response_model=UserPublic)
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    tenant_id, branch_id = current_user.tenant_id, current_user.branch_id
    if req.role not in [UserRole.DOCTOR, UserRole.RECEPTIONIST]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phase 1 supports only Doctor and Receptionist clinic users.")
    user_repo = SQLAlchemyUserRepository(db)
    auth_service = AuthService(user_repo)
    try:
        user = auth_service.register_user(
            tenant_id=tenant_id,
            branch_id=branch_id,
            username=req.username,
            password=req.password,
            full_name=req.full_name,
            role=req.role,
            mobile=req.mobile,
            can_collect_payment=req.can_collect_payment,
            can_enter_vitals=req.can_enter_vitals,
            can_view_clinical_history=req.can_view_clinical_history,
            can_edit_clinical_data=req.can_edit_clinical_data
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    context: tuple[str, str] = Depends(get_tenant_context)
):
    tenant_id, branch_id = context
    client_ip = request.client.host if request.client else None
    user_repo = SQLAlchemyUserRepository(db)
    auth_service = AuthService(user_repo)
    audit_service = AuditService(db)
    
    from datetime import datetime
    user = auth_service.authenticate_user(tenant_id, form_data.username, form_data.password)
    if user and user.role == UserRole.SUPERDOC:
        audit_service.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=user.id,
            user_role=user.role.value,
            action="LOGIN_REJECTED",
            module="AUTH",
            record_id=user.id,
            summary="Login rejected: deprecated legacy role",
            ip_address=client_ip
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This legacy role is not supported in Phase 1. Please use Admin, Doctor or Receptionist.")
    if not user:
        audit_service.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=form_data.username,
            user_role=None,
            action="LOGIN_FAILED",
            module="AUTH",
            record_id=form_data.username,
            summary=f"Failed login attempt for username: {form_data.username}",
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Save last login timestamp
    user.last_login = datetime.utcnow()
    user_repo.save(user)
    
    # Create access token carrying tenant, branch, and role context
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value,
        "tenant_id": user.tenant_id,
        "branch_id": user.branch_id
    }
    access_token = auth_service.create_access_token(token_data)
    
    # Audit log successful login
    audit_service.record(
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=user.id,
        user_role=user.role.value,
        action="LOGIN_PASSWORD_SUCCESS",
        module="AUTH",
        record_id=user.id,
        summary=f"User {user.username} successfully signed in with password",
        ip_address=client_ip
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value,
        "username": user.username,
        "full_name": user.full_name,
        "can_collect_payment": user.can_collect_payment,
        "can_enter_vitals": user.can_enter_vitals,
        "can_view_clinical_history": user.can_view_clinical_history,
        "can_edit_clinical_data": user.can_edit_clinical_data,
        "user_id": user.id
    }

class OTPRequest(BaseModel):
    username_or_mobile: str

class OTPVerifyRequest(BaseModel):
    username_or_mobile: str
    otp: str

@router.post("/otp/request")
def request_otp(
    req: OTPRequest,
    db: Session = Depends(get_db),
    context: tuple[str, str] = Depends(get_tenant_context)
):
    tenant_id, branch_id = context
    user_repo = SQLAlchemyUserRepository(db)
    auth_service = AuthService(user_repo)
    try:
        return auth_service.request_login_otp(tenant_id, req.username_or_mobile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(
    request: Request,
    req: OTPVerifyRequest,
    db: Session = Depends(get_db),
    context: tuple[str, str] = Depends(get_tenant_context)
):
    tenant_id, branch_id = context
    client_ip = request.client.host if request.client else None
    user_repo = SQLAlchemyUserRepository(db)
    auth_service = AuthService(user_repo)
    audit_service = AuditService(db)
    try:
        user = auth_service.verify_login_otp(tenant_id, req.username_or_mobile, req.otp)
    except ValueError as e:
        audit_service.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=req.username_or_mobile,
            user_role=None,
            action="OTP_VERIFY_FAILED",
            module="AUTH",
            record_id=req.username_or_mobile,
            summary=f"Failed OTP verification: {str(e)}",
            ip_address=client_ip
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    from datetime import datetime
    user.last_login = datetime.utcnow()
    user_repo.save(user)

    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value,
        "tenant_id": user.tenant_id,
        "branch_id": user.branch_id
    }
    access_token = auth_service.create_access_token(token_data)

    # Audit log successful OTP login
    audit_service.record(
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=user.id,
        user_role=user.role.value,
        action="LOGIN_OTP_SUCCESS",
        module="AUTH",
        record_id=user.id,
        summary=f"User {user.username} successfully signed in via OTP",
        ip_address=client_ip
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value,
        "username": user.username,
        "full_name": user.full_name,
        "can_collect_payment": user.can_collect_payment,
        "can_enter_vitals": user.can_enter_vitals,
        "can_view_clinical_history": user.can_view_clinical_history,
        "can_edit_clinical_data": user.can_edit_clinical_data,
        "user_id": user.id
    }

@router.post("/logout")
def logout(
    request: Request,
    reason: Optional[str] = "user_logout",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]))
):
    client_ip = request.client.host if request.client else None
    audit_service = AuditService(db)
    is_timeout = (reason == "inactivity_timeout")
    action_name = "SESSION_TIMEOUT" if is_timeout else "LOGOUT"
    summary_text = (
        f"User {current_user.username} session expired after 15 minutes of inactivity (HIPAA/DPDP Timeout)"
        if is_timeout else f"User {current_user.username} logged out"
    )
    audit_service.record(
        tenant_id=current_user.tenant_id,
        branch_id=current_user.branch_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        action=action_name,
        module="AUTH",
        record_id=current_user.id,
        summary=summary_text,
        ip_address=client_ip
    )
    return {"status": "logged_out", "reason": reason}

class UpdatePermissionsRequest(BaseModel):
    can_collect_payment: bool
    can_enter_vitals: bool
    can_view_clinical_history: bool
    can_edit_clinical_data: bool
    status: str

@router.get("/doctors", response_model=list[UserPublic])
def list_doctors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]))
):
    tenant_id, branch_id = current_user.tenant_id, current_user.branch_id
    user_repo = SQLAlchemyUserRepository(db)
    all_users = user_repo.list_by_branch(tenant_id, branch_id)
    return [u for u in all_users if u.role == UserRole.DOCTOR and u.status == "Active"]

@router.get("/me", response_model=UserPublic)
def current_session_user(current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]))):
    """Return the authenticated user; used by the desktop UI to validate a cached session."""
    return current_user

@router.get("/users", response_model=list[UserPublic])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    tenant_id = current_user.tenant_id
    branch_id = current_user.branch_id
    user_repo = SQLAlchemyUserRepository(db)
    return [u for u in user_repo.list_by_branch(tenant_id, branch_id) if u.role in [UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]]

@router.post("/users/{user_id}/permissions", response_model=UserPublic)
def update_user_permissions(
    request: Request,
    user_id: str,
    req: UpdatePermissionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    from datetime import datetime
    tenant_id = current_user.tenant_id
    user_repo = SQLAlchemyUserRepository(db)
    user = user_repo.find_by_id(user_id, tenant_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    user.can_collect_payment = req.can_collect_payment
    user.can_enter_vitals = req.can_enter_vitals
    user.can_view_clinical_history = req.can_view_clinical_history
    user.can_edit_clinical_data = req.can_edit_clinical_data
    user.status = req.status
    user.updated_at = datetime.utcnow()
    
    saved_user = user_repo.save(user)
    AuditService(db).record(
        tenant_id=tenant_id,
        branch_id=current_user.branch_id,
        user_id=current_user.id,
        user_role=current_user.role.value,
        action="UPDATE_USER_PERMISSIONS",
        module="AUTH",
        record_id=user.id,
        summary=f"Admin {current_user.username} modified permissions for staff user {user.username} (status: {user.status})",
        ip_address=request.client.host if request.client else None
    )
    return saved_user
