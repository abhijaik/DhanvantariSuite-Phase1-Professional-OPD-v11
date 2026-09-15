from abc import ABC, abstractmethod
from src.domain.models.invoice import Invoice
from src.domain.models.consultation import Consultation
from src.domain.models.patient import Patient

class DocGenPort(ABC):
    @abstractmethod
    def generate_invoice_pdf(self, invoice: Invoice, patient: Patient, language: str) -> bytes:
        """Generates invoice receipt PDF bytes. Language can be 'en', 'hi', or 'mr'."""
        pass

    @abstractmethod
    def generate_prescription_pdf(self, consultation: Consultation, patient: Patient, language: str) -> bytes:
        """Generates prescription record PDF bytes. Language can be 'en', 'hi', or 'mr'."""
        pass
