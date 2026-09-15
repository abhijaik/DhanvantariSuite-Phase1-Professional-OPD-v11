from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional

from src.adapters.api.dependencies import get_db, require_role, require_payment_collection
from src.adapters.db.repositories import (
    SQLAlchemyInvoiceRepository, SQLAlchemyPatientRepository, SQLAlchemyAppointmentRepository
)
from src.adapters.db.orm_models import AppointmentORM, InvoiceORM
from src.adapters.docgen.pdf_generator import PDFGeneratorAdapter
from src.services.billing_service import BillingService
from src.domain.models.user import UserRole, User
from src.domain.models.invoice import Invoice, InvoiceItem, PaymentMode, PaymentStatus

router = APIRouter(prefix="/api/billing", tags=["Billing & Invoicing"])

class CreateInvoiceRequest(BaseModel):
    appointment_id: str
    items: List[InvoiceItem]
    consultation_charges: Decimal = Decimal("0.00")
    medicine_charges: Decimal = Decimal("0.00")
    lab_charges: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    payment_mode: PaymentMode = PaymentMode.CASH
    payment_status: PaymentStatus = PaymentStatus.PENDING

class PayInvoiceRequest(BaseModel):
    payment_mode: PaymentMode
    amount: Optional[Decimal] = None

@router.post("/invoice", response_model=Invoice)
def create_invoice(
    req: CreateInvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_payment_collection())
):
    tenant_id = current_user.tenant_id
    branch_id = current_user.branch_id
    
    invoice_repo = SQLAlchemyInvoiceRepository(db)
    patient_repo = SQLAlchemyPatientRepository(db)
    appt_repo = SQLAlchemyAppointmentRepository(db)
    doc_gen = PDFGeneratorAdapter()
    
    billing_service = BillingService(invoice_repo, patient_repo, appt_repo, doc_gen)
    
    try:
        return billing_service.create_invoice(
            tenant_id=tenant_id,
            branch_id=branch_id,
            appointment_id=req.appointment_id,
            items=req.items,
            consultation_charges=req.consultation_charges,
            medicine_charges=req.medicine_charges,
            lab_charges=req.lab_charges,
            discount_amount=req.discount_amount,
            payment_mode=req.payment_mode,
            payment_status=req.payment_status
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/invoice/{invoice_id}/pay", response_model=Invoice)
def pay_invoice(
    invoice_id: str,
    req: PayInvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_payment_collection())
):
    tenant_id = current_user.tenant_id
    
    invoice_repo = SQLAlchemyInvoiceRepository(db)
    patient_repo = SQLAlchemyPatientRepository(db)
    appt_repo = SQLAlchemyAppointmentRepository(db)
    doc_gen = PDFGeneratorAdapter()
    
    billing_service = BillingService(invoice_repo, patient_repo, appt_repo, doc_gen)
    try:
        return billing_service.record_payment(invoice_id, tenant_id, req.payment_mode, req.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/pending-visits")
def pending_billing_visits(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_payment_collection())
):
    from src.domain.models.appointment import AppointmentStatus
    appts = db.query(AppointmentORM).filter(
        AppointmentORM.tenant_id == current_user.tenant_id,
        AppointmentORM.branch_id == current_user.branch_id,
        AppointmentORM.status == AppointmentStatus.COMPLETED.value
    ).order_by(AppointmentORM.updated_at.desc()).all()
    patient_repo = SQLAlchemyPatientRepository(db)
    invoice_repo = SQLAlchemyInvoiceRepository(db)
    out=[]
    for a in appts:
        if invoice_repo.find_by_appointment_id(a.id, current_user.tenant_id):
            continue
        p=patient_repo.find_by_id(a.patient_id,current_user.tenant_id)
        out.append({"appointment": {
            "id": a.id, "tenant_id": a.tenant_id, "branch_id": a.branch_id, "patient_id": a.patient_id,
            "doctor_id": a.doctor_id, "appointment_date": a.appointment_date, "scheduled_time": a.scheduled_time,
            "status": a.status, "queue_token": a.queue_token, "visit_type": a.visit_type,
            "consultation_type": a.consultation_type, "consultation_subtype": a.consultation_subtype, "notes": a.notes,
            "created_at": a.created_at, "updated_at": a.updated_at
        }, "patient": p.model_dump(mode="json") if p else None})
    return out

@router.get("/invoices")
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]))
):
    repo=SQLAlchemyInvoiceRepository(db)
    return [i.model_dump(mode="json") for i in repo.list_by_branch(current_user.tenant_id,current_user.branch_id)]

@router.get("/invoice/{invoice_id}/print")
def print_invoice(
    invoice_id: str,
    lang: str = "en",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST]))
):
    tenant_id = current_user.tenant_id
    invoice_repo = SQLAlchemyInvoiceRepository(db)
    patient_repo = SQLAlchemyPatientRepository(db)
    appt_repo = SQLAlchemyAppointmentRepository(db)
    doc_gen = PDFGeneratorAdapter()
    
    billing_service = BillingService(invoice_repo, patient_repo, appt_repo, doc_gen)
    try:
        pdf_bytes = billing_service.generate_receipt_pdf(invoice_id, tenant_id, lang)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
