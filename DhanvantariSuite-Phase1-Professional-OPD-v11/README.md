# Dhanvantari Clinic ERP — Professional OPD Edition

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)]()

## 1. Product Overview
**Dhanvantari Clinic ERP** is a modern outpatient department (OPD), consultation, and billing platform designed for single-doctor clinics and multi-doctor polyclinics/hospitals. It operates under a **Unified Engine Hybrid Deployment** model: the exact same codebase and architecture runs seamlessly as a **Multi-Tenant Cloud SaaS** or as a **Standalone Desktop Application** (via PyWebView).

---

## 2. Key Features

- **Dual-Mode Secure Authentication**:
  - **Password Login**: Traditional bcrypt salted password validation.
  - **OTP Login**: 6-digit one-time password sent to registered username or 10-digit mobile number with 5-minute expiry and brute-force protection.
- **Multilingual Support & RTL**:
  - UI natively supports **English (EN)**, **मराठी (MR)**, **हिंदी (HI)**, and **العربية (AR)**.
  - Automatic Right-to-Left (RTL) layout switching when Arabic is selected.
- **Multilingual PDF Prescription Generation**:
  - Prescriptions can be printed in English, Marathi, Hindi, or Arabic on demand.
  - **Pharmaceutical Safety Guard**: Medicine names are strictly preserved in English/Latin brand names while clinical sections, vitals, food relations, dosage, and instructions are translated.
  - Integrated Devanagari TrueType font rendering and Arabic bidirectional contextual reshaping (`arabic-reshaper` + `python-bidi`).
- **Real-Time Synchronized OPD Dashboard**:
  - Live 5-stat KPI summary: **Today's Patients**, **Checked In**, **In Consultation**, **Completed Patients**, and **Scheduled**.
  - 3-second live synchronization keeps Receptionist, Nurse, and Doctor dashboards updated in real time without page reloads.
  - Doctors can check in arriving patients directly from their dashboard.
  - Completed patients remain in the daily encounter queue with quick actions for payment collection and prescription viewing.
- **Comprehensive Clinical Workflows**:
  - Complete vitals recording with automated BMI calculation.
  - Chief complaints, clinical findings, provisional diagnosis, and Rx formulation.
  - Itemized invoicing and multi-mode payment collection (Cash, Card, UPI, etc.).
- **Multi-Tenant SaaS Data Isolation**:
  - Composite indexing on `(tenant_id, branch_id)` ensures logical isolation across clinics in cloud mode, with transparent `local-clinic` injection for standalone desktop mode.

---

## 3. Roles & Access Matrix

- **Admin**: System configuration, user management, audit trails, reports, and billing oversight.
- **Receptionist**: Patient registration, appointment scheduling, check-in, queue management, and billing/payment collection.
- **Doctor**: Clinical consultations, vitals, prescriptions, direct patient check-in, and own queue management.
- **Doctor_All**: Super-user clinician access with permission to view and consult patients across all clinic doctors.

---

## 4. Documentation

- [User Guide (USER_GUIDE.md)](USER_GUIDE.md): Step-by-step instructions for front-desk staff, clinicians, and administrators.
- [System Architecture (ARCHITECTURE.md)](ARCHITECTURE.md): Comprehensive hexagonal architecture, subsystem design, data isolation, and state machine specifications.
- [Version 11 Changes (PROFESSIONAL_OPD_V11_CHANGES.md)](PROFESSIONAL_OPD_V11_CHANGES.md): Detailed changelog of latest features and enhancements.

---

## 5. Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL (or local SQLite for automated testing/standalone mode)

### Installation
```powershell
# Clone or open the repository directory
cd DhanvantariSuite-Phase1-Professional-OPD-v11

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### Database Initialization
```powershell
# Optional: Set your PostgreSQL connection string (defaults to SQLite if unset)
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/clinic_erp"

# Initialize tables and seed default users
python init_db.py
```

### Running the Application

#### Option A: Web Server Mode (SaaS / LAN)
```powershell
# Start Uvicorn ASGI server
python -m uvicorn src.main:app --reload --port 8000
```
Open your browser at: `http://127.0.0.1:8000/ui/`

#### Option B: Desktop Shell Mode
```powershell
# Run using the provided launcher
.\start_client.bat
```

---

## 6. Default Demo Credentials
When the database is newly initialized, the following demo accounts are created:

| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin** | `admin_user` | `adminpass123` |
| **Receptionist** | `receptionist_user` | `receppass123` |
| **Doctor** | `doctor_user` | `docpass123` |

*(Users can also log in via OTP using these usernames or their registered mobile numbers).*

---

## 7. Running Automated Tests
```powershell
# Run the complete test suite
pytest
```
