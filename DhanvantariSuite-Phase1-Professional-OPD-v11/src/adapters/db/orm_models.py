from datetime import date, time, datetime
from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Time, DateTime, Text, Numeric, Boolean, ForeignKey, UniqueConstraint, Integer, Float, Index
from decimal import Decimal

class Base(DeclarativeBase):
    pass

class UserORM(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "username", name="uq_user_tenant_username"),
        Index("ix_users_tenant_branch", "tenant_id", "branch_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    branch_id: Mapped[str] = mapped_column(String(36), index=True)
    username: Mapped[str] = mapped_column(String(50), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))
    mobile: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    can_collect_payment: Mapped[bool] = mapped_column(Boolean, default=True)
    can_enter_vitals: Mapped[bool] = mapped_column(Boolean, default=True)
    can_view_clinical_history: Mapped[bool] = mapped_column(Boolean, default=True)
    can_edit_clinical_data: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="Active")
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PatientORM(Base):
    __tablename__ = "patients"
    __table_args__ = (
        UniqueConstraint("tenant_id", "patient_number", name="uq_patient_tenant_number"),
        UniqueConstraint("tenant_id", "mobile_normalized", name="uq_patient_tenant_mobile"),
        Index("ix_patients_tenant_branch", "tenant_id", "branch_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    branch_id: Mapped[str] = mapped_column(String(36), index=True)
    patient_number: Mapped[str] = mapped_column(String(20), index=True)
    registration_date: Mapped[date] = mapped_column(Date)
    full_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[date] = mapped_column(Date)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(10))
    mobile_normalized: Mapped[str] = mapped_column(String(15), index=True)
    alternate_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[str] = mapped_column(Text)
    blood_group: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    marital_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    medical_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    referred_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AppointmentORM(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_tenant_branch", "tenant_id", "branch_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    branch_id: Mapped[str] = mapped_column(String(36), index=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"))
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    appointment_date: Mapped[date] = mapped_column(Date, index=True)
    scheduled_time: Mapped[time] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(20))
    queue_token: Mapped[str] = mapped_column(String(10))
    visit_type: Mapped[str] = mapped_column(String(20))
    consultation_type: Mapped[str] = mapped_column(String(20))
    consultation_subtype: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    referred_by_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    referred_by_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConsultationORM(Base):
    __tablename__ = "consultations"
    __table_args__ = (
        Index("ix_consultations_tenant_branch", "tenant_id", "branch_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    branch_id: Mapped[str] = mapped_column(String(36), index=True)
    appointment_id: Mapped[str] = mapped_column(String(36), ForeignKey("appointments.id"), unique=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"))
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    consultation_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    consultation_subtype: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    symptoms: Mapped[str] = mapped_column(Text) # Stored as serialized JSON list
    diagnosis: Mapped[str] = mapped_column(Text)
    prescription_json: Mapped[str] = mapped_column(Text) # Stored as serialized JSON list of medicines
    blood_pressure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bmi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pulse_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spo2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    respiratory_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class InvoiceORM(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "invoice_number", name="uq_invoice_tenant_number"),
        Index("ix_invoices_tenant_branch", "tenant_id", "branch_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    branch_id: Mapped[str] = mapped_column(String(36), index=True)
    appointment_id: Mapped[str] = mapped_column(String(36), ForeignKey("appointments.id"), unique=True)
    invoice_number: Mapped[str] = mapped_column(String(20), index=True)
    items_json: Mapped[str] = mapped_column(Text) # Stored as serialized JSON array of line items
    consultation_charges: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    medicine_charges: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    lab_charges: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    payment_mode: Mapped[str] = mapped_column(String(20))
    payment_status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VitalsConfigORM(Base):
    __tablename__ = "vitals_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    branch_id: Mapped[str] = mapped_column(String(36), index=True)
    recorder_role: Mapped[str] = mapped_column(String(20)) # RECEPTIONIST, NURSE, DOCTOR, ANY
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AppointmentVitalsORM(Base):
    __tablename__ = "appointment_vitals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    branch_id: Mapped[str] = mapped_column(String(36), index=True)
    appointment_id: Mapped[str] = mapped_column(String(36), ForeignKey("appointments.id"), unique=True)
    blood_pressure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bmi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pulse: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spo2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    respiratory_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recorded_by: Mapped[str] = mapped_column(String(100))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class SyncLogORM(Base):
    __tablename__ = "sync_transaction_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    table_name: Mapped[str] = mapped_column(String(50))
    record_id: Mapped[str] = mapped_column(String(36))
    operation: Mapped[str] = mapped_column(String(10))
    payload: Mapped[str] = mapped_column(Text) # Serialized JSON string of the record at the time of modification
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    synced: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

class ClinicSettingsORM(Base):
    __tablename__ = "clinic_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    branch_id: Mapped[str] = mapped_column(String(36), index=True)
    clinic_name: Mapped[str] = mapped_column(String(100))
    clinic_address: Mapped[str] = mapped_column(Text)
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    license_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    tax_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    invoice_prefix: Mapped[str] = mapped_column(String(10), default="INV")
    invoice_language_default: Mapped[str] = mapped_column(String(10), default="en")
    appointment_duration: Mapped[int] = mapped_column(Integer, default=15)
    vitals_entry_by: Mapped[str] = mapped_column(String(20), default="Both")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLogORM(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    branch_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(50))
    module: Mapped[str] = mapped_column(String(50))
    record_id: Mapped[str] = mapped_column(String(36), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    summary: Mapped[str] = mapped_column(Text)
