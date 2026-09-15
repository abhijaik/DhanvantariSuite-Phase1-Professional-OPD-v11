import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from src.domain.models.invoice import Invoice, InvoiceItem, PaymentMode, PaymentStatus
from src.domain.ports.invoice_repository import InvoiceRepository
from src.domain.ports.doc_gen_port import DocGenPort
from src.domain.ports.patient_repository import PatientRepository
from src.domain.ports.appointment_repository import AppointmentRepository

class BillingService:
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        patient_repo: PatientRepository,
        appointment_repo: AppointmentRepository,
        doc_gen_port: DocGenPort
    ):
        self.invoice_repo = invoice_repo
        self.patient_repo = patient_repo
        self.appointment_repo = appointment_repo
        self.doc_gen_port = doc_gen_port

    def create_invoice(
        self,
        tenant_id: str,
        branch_id: str,
        appointment_id: str,
        items: List[InvoiceItem],
        consultation_charges: Decimal = Decimal("0.00"),
        medicine_charges: Decimal = Decimal("0.00"),
        lab_charges: Decimal = Decimal("0.00"),
        discount_amount: Decimal = Decimal("0.00"),
        payment_mode: PaymentMode = PaymentMode.CASH,
        payment_status: PaymentStatus = PaymentStatus.PENDING
    ) -> Invoice:
        # Check if invoice already exists for this appointment
        existing = self.invoice_repo.find_by_appointment_id(appointment_id, tenant_id)
        if existing:
            raise ValueError("Invoice already generated for this appointment")

        # Calculate totals
        subtotal = consultation_charges + medicine_charges + lab_charges
        tax_amount = Decimal("0.00")
        for item in items:
            item_total_before_tax = item.unit_price * item.quantity
            item_tax = (item_total_before_tax * item.tax_rate) / Decimal("100.00")
            item.tax_amount = item_tax
            item.total = item_total_before_tax + item_tax
            
            subtotal += item_total_before_tax
            tax_amount += item_tax

        total_amount = subtotal + tax_amount - discount_amount
        if total_amount < 0:
            total_amount = Decimal("0.00")

        # Handle initial paid state
        amount_paid = Decimal("0.00")
        if payment_status == PaymentStatus.PAID:
            amount_paid = total_amount
        amount_due = total_amount - amount_paid

        # Generate sequential invoice number (e.g. INV-YYMMDD-XXXX)
        import random
        random_suffix = random.randint(1000, 9999)
        invoice_num = f"INV-{datetime.now().strftime('%y%m%d')}-{random_suffix}"

        invoice = Invoice(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            branch_id=branch_id,
            appointment_id=appointment_id,
            invoice_number=invoice_num,
            items=items,
            consultation_charges=consultation_charges,
            medicine_charges=medicine_charges,
            lab_charges=lab_charges,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            amount_paid=amount_paid,
            amount_due=amount_due,
            payment_mode=payment_mode,
            payment_status=payment_status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return self.invoice_repo.save(invoice)

    def record_payment(
        self,
        invoice_id: str,
        tenant_id: str,
        payment_mode: PaymentMode,
        payment_amount: Optional[Decimal] = None
    ) -> Invoice:
        invoice = self.invoice_repo.find_by_id(invoice_id, tenant_id)
        if not invoice:
            raise ValueError("Invoice not found")

        if payment_amount is None:
            # Pay full remaining balance
            payment_amount = invoice.amount_due

        invoice.amount_paid += payment_amount
        if invoice.amount_paid >= invoice.total_amount:
            invoice.amount_paid = invoice.total_amount
            invoice.amount_due = Decimal("0.00")
            invoice.payment_status = PaymentStatus.PAID
        elif invoice.amount_paid > 0:
            invoice.amount_due = invoice.total_amount - invoice.amount_paid
            invoice.payment_status = PaymentStatus.PARTIAL
        else:
            invoice.amount_due = invoice.total_amount
            invoice.payment_status = PaymentStatus.PENDING

        invoice.payment_mode = payment_mode
        invoice.updated_at = datetime.utcnow()
        return self.invoice_repo.save(invoice)

    def generate_receipt_pdf(self, invoice_id: str, tenant_id: str, language: str) -> bytes:
        invoice = self.invoice_repo.find_by_id(invoice_id, tenant_id)
        if not invoice:
            raise ValueError("Invoice not found")

        # Find appointment and patient
        appointment = self.appointment_repo.find_by_id(invoice.appointment_id, tenant_id)
        if not appointment:
            raise ValueError("Appointment not found")

        patient = self.patient_repo.find_by_id(appointment.patient_id, tenant_id)
        if not patient:
            raise ValueError("Patient not found")

        return self.doc_gen_port.generate_invoice_pdf(invoice, patient, language)
