from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.models.invoice import Invoice

class InvoiceRepository(ABC):
    @abstractmethod
    def save(self, invoice: Invoice) -> Invoice:
        pass

    @abstractmethod
    def find_by_id(self, invoice_id: str, tenant_id: str) -> Optional[Invoice]:
        pass

    @abstractmethod
    def find_by_appointment_id(self, appointment_id: str, tenant_id: str) -> Optional[Invoice]:
        pass

    @abstractmethod
    def find_by_invoice_number(self, invoice_number: str, tenant_id: str) -> Optional[Invoice]:
        pass

    @abstractmethod
    def list_by_branch(self, tenant_id: str, branch_id: str) -> List[Invoice]:
        pass
