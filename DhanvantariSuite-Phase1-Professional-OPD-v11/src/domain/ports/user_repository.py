from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.models.user import User

class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def find_by_id(self, user_id: str, tenant_id: str) -> Optional[User]:
        pass

    @abstractmethod
    def find_by_username(self, username: str, tenant_id: str) -> Optional[User]:
        pass

    @abstractmethod
    def list_by_branch(self, tenant_id: str, branch_id: str) -> List[User]:
        pass
