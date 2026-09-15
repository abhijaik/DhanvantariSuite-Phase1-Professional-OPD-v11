import uuid
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
import bcrypt

from src.domain.models.user import User, UserRole
from src.domain.ports.user_repository import UserRepository

# JWT configuration
SECRET_KEY = "SUPER_SECRET_CLINIC_ERP_KEY" # In production, load from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 # 8 hours (typical shift duration)

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def hash_password(self, password: str) -> str:
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pwd_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(pwd_bytes, hash_bytes)
        except Exception:
            return False

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def register_user(
        self,
        tenant_id: str,
        branch_id: str,
        username: str,
        password: str,
        full_name: str,
        role: UserRole,
        mobile: Optional[str] = None,
        can_collect_payment: bool = True,
        can_enter_vitals: bool = True,
        can_view_clinical_history: bool = True,
        can_edit_clinical_data: bool = True
    ) -> User:
        # Check if username exists
        existing = self.user_repo.find_by_username(username, tenant_id)
        if existing:
            raise ValueError("Username already exists in this tenant")

        password_hash = self.hash_password(password)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            mobile=mobile,
            can_collect_payment=can_collect_payment,
            can_enter_vitals=can_enter_vitals,
            can_view_clinical_history=can_view_clinical_history,
            can_edit_clinical_data=can_edit_clinical_data,
            status="Active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return self.user_repo.save(user)

    def authenticate_user(self, tenant_id: str, username: str, password: str) -> Optional[User]:
        user = self.user_repo.find_by_username(username, tenant_id)
        if not user:
            return None
        if user.status != "Active":
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
