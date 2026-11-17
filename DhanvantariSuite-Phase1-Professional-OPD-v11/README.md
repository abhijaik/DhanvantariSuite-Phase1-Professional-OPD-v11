# Dhanvantari Clinic ERP — Professional OPD Edition

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)]()

## 1. Product Overview
**Dhanvantari Clinic ERP** is a modern outpatient department (OPD), consultation, diagnostic reports, and billing platform designed for single-doctor clinics and multi-doctor polyclinics/hospitals. It operates under a **Unified Engine Hybrid Deployment** model: the exact same codebase and architecture runs seamlessly as a **Multi-Tenant Cloud SaaS**, a **Progressive Web App (PWA)** on tablets and phones, or as a **Standalone Desktop Application** (via PyWebView / LAN host).

---

## 2. Key Features

- **Patient Diagnostic & Lab Reports Management**:
  - Centralized storage linked directly to patient medical history.
  - 4 flexible upload methods: **Direct File Upload** (PDF, JPG, PNG up to 25MB), **Google Drive Link** (with automatic iframe preview conversion), **Camera / Mobile Scan** (direct photo capture on phones/tablets), and **External Cloud Link**.
  - In-modal interactive document previewer (PDF viewer, full-screen image viewer, Google Drive embed) and secure file download.
  - 1-click access shortcuts right inside the Doctor Consultation cabin.

- **Doctor Clinical Analytics & Practice Reports**:
  - Dedicated doctor-only analytics suite with custom date filtering (Today, Week, Month, Custom).
  - 6 analytical modules: **OPD Volume Summary**, **Follow-Up Tracker** (Upcoming, Due Today, Overdue with WhatsApp links), **Top Diagnoses & Symptoms**, **Most Prescribed Medicines**, **Revenue Breakdown by Payment Mode**, and **Referral Partner Tracking**.
  - 1-click **Export to CSV** for offline spreadsheet analysis.

- **WhatsApp-Style Periodic Database Backup & Disaster Recovery**:
  - Portable compressed `.dhanbackup` archive specification bundling database tables and all uploaded patient files.
  - Automated 24-hour periodic daily backup checks with rolling 7-day retention.
  - 1-click **Backup Now** manual snapshot creation and download.
  - Complete disaster recovery **Restore from File** for reinstallations or PC migration with zero data loss.

- **3 Professional Healthcare Color Themes**:
  - 🌊 **Ocean Blue** *(Default)*: Authoritative sapphire clinical standard.
  - 🌿 **Emerald Health**: Fresh botanical surgical teal and mint green (reduces eye strain during long OPD shifts).
  - 👑 **Royal Indigo**: Modern specialty hospital indigo-violet.
  - Live real-time switcher on both the Login/Home page and Topbar with `localStorage` persistence.

- **Progressive Web App (PWA) & Mobile/Tablet Support**:
  - Offline app shell caching via Service Worker (`/ui/sw.js`) and Web Manifest (`/ui/manifest.json`).
  - Mobile sliding navigation drawer and touch-friendly interface.

- **Dual-Mode Secure Authentication**:
  - **Password Login**: Traditional bcrypt salted password validation.
  - **OTP Login**: 6-digit one-time password sent to registered username or 10-digit mobile number with 5-minute expiry and brute-force protection.

- **Multilingual Support & RTL Integration**:
  - UI natively supports **English (EN)**, **मराठी (MR)**, **हिंदी (HI)**, and **العربية (AR)**.
  - Automatic Right-to-Left (RTL) layout switching when Arabic is selected.

- **Multilingual PDF Prescription Generation**:
  - Prescriptions can be printed in English, Marathi, Hindi, or Arabic on demand.
  - **Pharmaceutical Safety Guard**: Medicine names are strictly preserved in English/Latin brand names to prevent dispensing errors, while all clinical findings, directions, vitals, and instructions are localized.

- **Real-Time Synchronized OPD Dashboard**:
  - Live 5-stat KPI summary: **Today's Patients**, **Checked In**, **In Consultation**, **Completed Patients**, and **Scheduled**.
  - 3-second live synchronization keeps Receptionist, Nurse, and Doctor dashboards updated in real time without page reloads.

- **HIPAA & DPDP Act 2023 Technical Safeguards**:
  - Comprehensive immutable Audit Trail accessible to Admins and Doctors.
  - 15-minute automatic session inactivity timeout with 60-second warning countdown.
  - AES-256 (Fernet) field-level database encryption at rest for patient PII and clinical notes.
  - Enforced HTTPS / TLS 1.3 with strict HTTP security headers (HSTS, CSP, anti-clickjacking).

---

## 3. Roles & Access Matrix

| Role | OPD Queue Access | Patient Registration | Start Consultation | View Doctor Reports | Audit Logs | Backup & Restore |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Admin** | View All | Yes | No (Read-Only) | Yes | Full View | Yes |
| **Receptionist** | View All | Yes | No | No | No | No |
| **Doctor** | Own Assigned Queue | Yes | Yes (Full Rx) | Yes | Full View | Yes |
| **Doctor_All** | View & Manage All | Yes | Yes (Any Patient) | Yes | Full View | Yes |

---

## 4. Documentation Index

- [User Guide (USER_GUIDE.md)](USER_GUIDE.md): Step-by-step instructions for front-desk staff, clinicians, and administrators.
- [System Architecture (ARCHITECTURE.md)](ARCHITECTURE.md): Comprehensive hexagonal architecture, subsystem design, data isolation, and state machine specifications.
- [Changelog & Release Notes (PROFESSIONAL_OPD_V11_CHANGES.md)](PROFESSIONAL_OPD_V11_CHANGES.md): Detailed changelog of features and technical enhancements.

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

#### Option A: Web Server / PWA Mode (SaaS / LAN)
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

### Running Automated Test Suite
```powershell
pytest tests/
```
