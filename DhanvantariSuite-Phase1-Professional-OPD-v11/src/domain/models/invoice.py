from enum import Enum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from decimal import Decimal

class PaymentMode(str, Enum):
    CASH = "CASH"
    UPI = "UPI"
    CARD = "CARD"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    REFUNDED = "REFUNDED"

class InvoiceItem(BaseModel):
    description: str
    quantity: int
    unit_price: Decimal
    tax_rate: Decimal = Decimal("0.00") # Tax rate percentage (e.g. 18.00)
    tax_amount: Decimal = Decimal("0.00")
    total: Decimal

class Invoice(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    appointment_id: str
    invoice_number: str
    items: List[InvoiceItem]
    consultation_charges: Decimal = Decimal("0.00")
    medicine_charges: Decimal = Decimal("0.00")
    lab_charges: Decimal = Decimal("0.00")
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal = Decimal("0.00")
    amount_due: Decimal = Decimal("0.00")
    payment_mode: PaymentMode
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
