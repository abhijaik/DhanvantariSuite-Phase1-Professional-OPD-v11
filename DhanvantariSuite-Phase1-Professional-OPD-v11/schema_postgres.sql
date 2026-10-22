-- ============================================================
-- Dhanvantari Clinic ERP - PostgreSQL Database Schema
-- Compatible with PostgreSQL 12+
-- Usage:
--   1. Create database:
--        CREATE DATABASE clinic_erp;
--   2. Apply schema:
--        psql -U postgres -d clinic_erp -f schema_postgres.sql
-- ============================================================

-- Table: audit_logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    branch_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    user_role VARCHAR(30),
    action VARCHAR(50) NOT NULL,
    module VARCHAR(50) NOT NULL,
    record_id VARCHAR(36) NOT NULL,
    ip_address VARCHAR(50),
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    summary TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_record_id ON audit_logs (record_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_tenant_id ON audit_logs (tenant_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_branch_id ON audit_logs (branch_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp ON audit_logs (timestamp);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id);

-- Table: clinic_settings
CREATE TABLE IF NOT EXISTS clinic_settings (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    branch_id VARCHAR(36) NOT NULL,
    clinic_name VARCHAR(100) NOT NULL,
    clinic_address TEXT NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    logo_url VARCHAR(255),
    license_number VARCHAR(100),
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    tax_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    invoice_prefix VARCHAR(10) NOT NULL DEFAULT 'INV',
    invoice_language_default VARCHAR(10) NOT NULL DEFAULT 'en',
    appointment_duration INTEGER NOT NULL DEFAULT 15,
    vitals_entry_by VARCHAR(20) NOT NULL DEFAULT 'Both',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_clinic_settings_tenant_id ON clinic_settings (tenant_id);
CREATE INDEX IF NOT EXISTS ix_clinic_settings_branch_id ON clinic_settings (branch_id);

-- Table: medicines
CREATE TABLE IF NOT EXISTS medicines (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(150) NOT NULL,
    generic_name VARCHAR(150),
    dosage_form VARCHAR(50) DEFAULT 'Tablet',
    default_timing VARCHAR(50),
    default_duration VARCHAR(50),
    default_food_relation VARCHAR(50),
    instructions VARCHAR(200),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_medicine_tenant_name UNIQUE (tenant_id, name)
);

CREATE INDEX IF NOT EXISTS ix_medicines_tenant_id ON medicines (tenant_id);
CREATE INDEX IF NOT EXISTS ix_medicines_name ON medicines (name);
CREATE INDEX IF NOT EXISTS ix_medicines_tenant_name ON medicines (tenant_id, name);

-- Table: patients
CREATE TABLE IF NOT EXISTS patients (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    branch_id VARCHAR(36) NOT NULL,
    patient_number VARCHAR(20) NOT NULL,
    registration_date DATE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(10) NOT NULL,
    mobile_normalized VARCHAR(15) NOT NULL,
    alternate_number TEXT,
    email TEXT,
    address TEXT NOT NULL,
    blood_group VARCHAR(10),
    marital_status VARCHAR(20),
    emergency_contact TEXT,
    allergies TEXT,
    medical_notes TEXT,
    referred_by VARCHAR(100),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_patient_tenant_number UNIQUE (tenant_id, patient_number),
    CONSTRAINT uq_patient_tenant_mobile UNIQUE (tenant_id, mobile_normalized)
);

CREATE INDEX IF NOT EXISTS ix_patients_branch_id ON patients (branch_id);
CREATE INDEX IF NOT EXISTS ix_patients_mobile_normalized ON patients (mobile_normalized);
CREATE INDEX IF NOT EXISTS ix_patients_patient_number ON patients (patient_number);
CREATE INDEX IF NOT EXISTS ix_patients_tenant_id ON patients (tenant_id);
CREATE INDEX IF NOT EXISTS ix_patients_tenant_branch ON patients (tenant_id, branch_id);

-- Table: sync_transaction_log
CREATE TABLE IF NOT EXISTS sync_transaction_log (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id VARCHAR(36) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    payload TEXT NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    synced BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_sync_transaction_log_tenant_id ON sync_transaction_log (tenant_id);
CREATE INDEX IF NOT EXISTS ix_sync_transaction_log_timestamp ON sync_transaction_log (timestamp);
CREATE INDEX IF NOT EXISTS ix_sync_transaction_log_synced ON sync_transaction_log (synced);

-- Table: users
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    branch_id VARCHAR(36) NOT NULL,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    mobile VARCHAR(20),
    can_collect_payment BOOLEAN NOT NULL DEFAULT TRUE,
    can_enter_vitals BOOLEAN NOT NULL DEFAULT TRUE,
    can_view_clinical_history BOOLEAN NOT NULL DEFAULT TRUE,
    can_edit_clinical_data BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    last_login TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_user_tenant_username UNIQUE (tenant_id, username)
);

CREATE INDEX IF NOT EXISTS ix_users_branch_id ON users (branch_id);
CREATE INDEX IF NOT EXISTS ix_users_tenant_branch ON users (tenant_id, branch_id);
CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users (tenant_id);

-- Table: vitals_configs
CREATE TABLE IF NOT EXISTS vitals_configs (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    branch_id VARCHAR(36) NOT NULL,
    recorder_role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_vitals_configs_tenant_id ON vitals_configs (tenant_id);
CREATE INDEX IF NOT EXISTS ix_vitals_configs_branch_id ON vitals_configs (branch_id);

-- Table: appointments
CREATE TABLE IF NOT EXISTS appointments (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    branch_id VARCHAR(36) NOT NULL,
    patient_id VARCHAR(36) NOT NULL,
    doctor_id VARCHAR(36) NOT NULL,
    appointment_date DATE NOT NULL,
    scheduled_time TIME WITHOUT TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL,
    queue_token VARCHAR(20) NOT NULL,
    visit_type VARCHAR(50) NOT NULL,
    consultation_type VARCHAR(100) NOT NULL,
    consultation_subtype VARCHAR(100),
    referred_by_type VARCHAR(50),
    referred_by_name VARCHAR(120),
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id),
    FOREIGN KEY(doctor_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS ix_appointments_branch_id ON appointments (branch_id);
CREATE INDEX IF NOT EXISTS ix_appointments_tenant_branch ON appointments (tenant_id, branch_id);
CREATE INDEX IF NOT EXISTS ix_appointments_appointment_date ON appointments (appointment_date);
CREATE INDEX IF NOT EXISTS ix_appointments_tenant_id ON appointments (tenant_id);

-- Table: appointment_vitals
CREATE TABLE IF NOT EXISTS appointment_vitals (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    branch_id VARCHAR(36) NOT NULL,
    appointment_id VARCHAR(36) NOT NULL,
    blood_pressure VARCHAR(20),
    weight FLOAT,
    height FLOAT,
    bmi FLOAT,
    temperature FLOAT,
    pulse INTEGER,
    spo2 INTEGER,
    respiratory_rate INTEGER,
    recorded_by VARCHAR(100) NOT NULL,
    recorded_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (appointment_id),
    FOREIGN KEY(appointment_id) REFERENCES appointments (id)
);

CREATE INDEX IF NOT EXISTS ix_appointment_vitals_branch_id ON appointment_vitals (branch_id);
CREATE INDEX IF NOT EXISTS ix_appointment_vitals_tenant_id ON appointment_vitals (tenant_id);

-- Table: consultations
CREATE TABLE IF NOT EXISTS consultations (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    branch_id VARCHAR(36) NOT NULL,
    appointment_id VARCHAR(36) NOT NULL,
    patient_id VARCHAR(36) NOT NULL,
    doctor_id VARCHAR(36) NOT NULL,
    consultation_type VARCHAR(100),
    consultation_subtype VARCHAR(100),
    symptoms TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    prescription_json TEXT NOT NULL,
    blood_pressure VARCHAR(20),
    weight FLOAT,
    height FLOAT,
    bmi FLOAT,
    temperature FLOAT,
    pulse_rate INTEGER,
    spo2 INTEGER,
    respiratory_rate INTEGER,
    follow_up_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (appointment_id),
    FOREIGN KEY(appointment_id) REFERENCES appointments (id),
    FOREIGN KEY(patient_id) REFERENCES patients (id),
    FOREIGN KEY(doctor_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS ix_consultations_tenant_branch ON consultations (tenant_id, branch_id);
CREATE INDEX IF NOT EXISTS ix_consultations_tenant_id ON consultations (tenant_id);
CREATE INDEX IF NOT EXISTS ix_consultations_branch_id ON consultations (branch_id);

-- Table: invoices
CREATE TABLE IF NOT EXISTS invoices (
    id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    branch_id VARCHAR(36) NOT NULL,
    appointment_id VARCHAR(36) NOT NULL,
    invoice_number VARCHAR(20) NOT NULL,
    items_json TEXT NOT NULL,
    consultation_charges NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    medicine_charges NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    lab_charges NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    subtotal NUMERIC(10, 2) NOT NULL,
    tax_amount NUMERIC(10, 2) NOT NULL,
    discount_amount NUMERIC(10, 2) NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    amount_paid NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    amount_due NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    payment_mode VARCHAR(20) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_invoice_tenant_number UNIQUE (tenant_id, invoice_number),
    UNIQUE (appointment_id),
    FOREIGN KEY(appointment_id) REFERENCES appointments (id)
);

CREATE INDEX IF NOT EXISTS ix_invoices_tenant_branch ON invoices (tenant_id, branch_id);
CREATE INDEX IF NOT EXISTS ix_invoices_tenant_id ON invoices (tenant_id);
CREATE INDEX IF NOT EXISTS ix_invoices_branch_id ON invoices (branch_id);
CREATE INDEX IF NOT EXISTS ix_invoices_invoice_number ON invoices (invoice_number);
