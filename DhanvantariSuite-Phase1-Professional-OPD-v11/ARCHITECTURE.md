# Dhanvantari Clinic ERP — System Architecture & Design Specification

## 1. Architectural Overview

Dhanvantari Clinic ERP is built on a **Hexagonal Architecture (Ports and Adapters / Clean Architecture)** design pattern. It operates under a **Unified Engine Hybrid Deployment** model, allowing the identical codebase to run either as a **Multi-Tenant Cloud SaaS** or as a **Single-Tenant Local Desktop Application** (via PyWebView / LAN host) without architectural branching.

```
+---------------------------------------------------------------------------------+
|                                 USER INTERFACES                                 |
|   +------------------------------------+   +--------------------------------+   |
|   |    Progressive Web App (PWA)       |   |    PyWebView Desktop Shell     |   |
|   |  (HTML5 / ES6 / Responsive Drawer  |   |   (Local Native Window Host)   |   |
|   |   3 Color Themes / RTL Layout)     |   |                                |   |
|   +------------------------------------+   +--------------------------------+   |
+---------------------------------------------------------------------------------+
                                       |
                                       v  HTTP / REST / JSON / Multipart
+---------------------------------------------------------------------------------+
|                       ADAPTERS LAYER — DRIVING (INBOUND)                        |
|   FastAPI REST Routers:                                                         |
|   - router_auth (JWT, Bcrypt, OTP)        - router_queue (Live OPD, Check-in)   |
|   - router_patient (Demographics, Search) - router_consultation (Clinical, Rx)  |
|   - router_billing (Invoices, Receipts)   - router_admin (Clinic Config, Users) |
|   - router_reports (Doctor Analytics)     - router_patient_reports (Lab Scans)  |
|   - router_backup (WhatsApp-Style DB)     - router_audit (HIPAA / DPDP Trail)   |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
|                                APPLICATION SERVICES                             |
|   - AuthService          (Password verification, OTP lifecycle, JWT generation) |
|   - QueueService         (Token generation, OPD state machine, live metrics)    |
|   - ConsultationService  (Clinical encounters, vitals, Rx management)          |
|   - BillingService       (Invoice calculation, payment receipting)              |
|   - BackupService        (Portable .dhanbackup snapshot, restore, auto-prune)   |
|   - AuditService         (Immutable compliance trail, auto-commit logging)      |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
|                                   DOMAIN CORE                                   |
|   - Domain Entities: Patient, Appointment, Consultation, Vitals, Invoice, User, |
|                      PatientReport, AuditLog, ClinicSettings                    |
|   - Ports (Interfaces):                                                         |
|     * UserRepository, PatientRepository, AppointmentRepository                  |
|     * ConsultationRepository, InvoiceRepository, DocGenPort                     |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
|                       ADAPTERS LAYER — DRIVEN (OUTBOUND)                        |
|   +----------------------------------+   +----------------------------------+   |
|   |    SQLAlchemy 2.0 Persistence    |   |     ReportLab Document Engine    |   |
|   |  (PostgreSQL Multi-Tenant DB)    |   |  (Multilingual Unicode PDF Gen)  |   |
|   +----------------------------------+   +----------------------------------+   |
|   +----------------------------------+   +----------------------------------+   |
|   |    Encrypted Tenant File Store   |   |   Zip / Deflate Backup Archive   |   |
|   |  (uploads/reports/{tenant_id})   |   |  (backups/{tenant_id}/*.backup)  |   |
|   +----------------------------------+   +----------------------------------+   |
+---------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

### 2.1 Hexagonal Layering & Dependency Inversion
- **Domain Core (`src/domain/`)**: Pure business models and repository ports. Has zero third-party dependencies (no FastAPI, no SQLAlchemy, no ReportLab).
- **Application Services (`src/services/`)**: Orchestrates business logic (e.g., verifying an OTP, calculating BMI, compiling clinic metrics, creating `.dhanbackup` archives).
- **Adapters (`src/adapters/`)**:
  - **Inbound Adapters (`src/adapters/api/`)**: Translates HTTP requests into service calls and returns clean Pydantic schema representations.
  - **Outbound Adapters (`src/adapters/db/`, `src/adapters/docgen/`)**: Implements persistence ports via SQLAlchemy ORM and document generation via ReportLab.

### 2.2 Multi-Tenant Data Isolation Strategy
- All relational tables incorporate `tenant_id` and `branch_id` columns.
- High-performance logical data isolation is achieved using composite indices:
  ```sql
  CREATE INDEX idx_patients_tenant_branch ON patients(tenant_id, branch_id);
  CREATE INDEX idx_appointments_tenant_branch_date ON appointments(tenant_id, branch_id, appointment_date);
  CREATE INDEX idx_patient_reports_tenant_pat ON patient_reports(tenant_id, patient_id);
  ```
- In cloud SaaS mode, `get_tenant_context` extracts `tenant_id` and `branch_id` from the validated JWT token and scopes all queries.
- In desktop mode, the system injects `local-clinic` transparently.

---

## 3. Subsystem Architecture

### 3.1 Authentication & Credential Provider
The authentication system supports dual credential validation paths:
- **Password Authentication**: Validates salted bcrypt password hashes.
- **OTP Authentication**:
  - Request endpoint (`POST /api/auth/otp/request`) looks up user by username or 10-digit mobile number.
  - Generates a cryptographically random 6-digit OTP stored with creation timestamp, expiration (300 seconds), and attempt counter.
  - Verify endpoint (`POST /api/auth/otp/verify`) checks code validity, enforces a maximum of 3 invalid attempts before invalidating the token, and issues standard JWT tokens.

### 3.2 Real-Time OPD Queue & State Machine

```
      +-------------+
      |  SCHEDULED  |  <--- Patient registered / Appointment booked
      +-------------+
             |
             | Receptionist or Doctor clicks "Check-in"
             v
      +-------------+
      | CHECKED_IN  |  <--- Waiting in clinic lobby; Token generated
      +-------------+
             |
             | Doctor clicks "Start Consultation"
             v
    +-----------------+
    | IN_CONSULTATION | <--- Patient inside doctor cabin
    +-----------------+
             |
             | Doctor clicks "Complete Consultation"
             v
      +-------------+
      |  COMPLETED  |  <--- Retained in daily queue; Invoice auto-created
      +-------------+
```

- **Persistent Footfall Tracking**: `list_queue` includes all appointment states (`SCHEDULED`, `CHECKED_IN`, `IN_CONSULTATION`, `COMPLETED`). Completing an appointment never deletes or hides it from the day's record.
- **5-Metric KPI Dashboard**:
  - `Today's Patients` = $\sum(\text{Scheduled} + \text{Checked In} + \text{In Consultation} + \text{Completed})$
  - `Checked In` = Patients waiting in lobby.
  - `In Consultation` = Patients currently with doctor.
  - `Completed Patients` = Visits concluded today.
  - `Scheduled` = Patients booked but not yet checked in.
- **Zero-Overhead Live Polling**: Frontend polls `GET /api/queue/live/details` every 3000ms. Eliminates WebSocket connection fragility across unstable clinic Wi-Fi while guaranteeing real-time updates.

### 3.3 Patient Diagnostic & Lab Reports Subsystem
- **Domain Entity**: `PatientReport` captures report metadata, category, date, doctor notes, and source reference.
- **Multi-Source Ingestion Pathways**:
  1. `FILE_UPLOAD`: Direct multipart file uploads (PDF, JPG, PNG, WEBP, DOCX up to 25MB). Stored safely on disk with path sanitization (`re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)`).
  2. `GOOGLE_DRIVE`: Shareable link binding. Automatically parses file IDs via regex `/(?:/d/|id=)([a-zA-Z0-9_-]{25,})/` and synthesizes embeddable iframe preview URLs (`/preview`).
  3. `CAMERA_SCAN`: Native mobile/tablet camera capture via `<input type="file" capture="environment">` for instant physical document scanning.
  4. `EXTERNAL_URL`: Links to external hospital portals, PACS systems, or cloud storage.
- **Secure File Serving & Path Traversal Guard**:
  - Files are served via `GET /api/patient-reports/{report_id}/file` with strict path verification ensuring canonical resolved paths remain inside `UPLOAD_ROOT / tenant_id`.
  - All access, preview, and download requests generate immutable compliance audit logs.

### 3.4 Doctor Analytics & Clinical Reports Subsystem
Restricted to `DOCTOR` and `DOCTOR_ALL` roles (`router_reports.py`). Computes live aggregates over customizable date ranges:
1. **OPD Summary**: Total patient volume, new vs. follow-up consults, and status breakdown.
2. **Follow-Up Tracker**: Categorizes upcoming, due today, and overdue patient follow-up dates.
3. **Diagnosis & Symptom Trends**: Frequency rank order of diagnoses and presenting symptoms for disease surveillance.
4. **Top Prescribed Medications**: Identifies the clinic's most frequently prescribed drugs and dosages.
5. **Revenue Breakdown**: Invoices billed, collected, and pending dues broken down by payment mode (Cash, UPI, Card).
6. **Referral Partner Tracking**: Volume analysis by referral source (Doctor, Hospital, Patient).
7. **CSV Streaming Export**: Browser-based RFC 4180 compliant CSV export for offline analysis in Excel.

### 3.5 WhatsApp-Style Database Backup & Disaster Recovery
- **Portable Clinic Archive (`.dhanbackup`)**:
  - Encapsulates entire clinic data into a single compressed ZIP archive.
  - `manifest.json`: Stores schema version, backup type (`AUTO` or `MANUAL`), timestamp, and exact record counts.
  - `database.json`: Full relational snapshot serializing Users, Patients, Appointments, Consultations, Invoices, Vitals, Clinic Settings, Patient Reports metadata, and Audit Logs.
  - `reports/`: Bundles all physical uploaded patient report files and scans.
- **Automated Periodic Scheduling (Like WhatsApp 2:00 AM)**:
  - Background checker (`POST /api/backup/auto-check`) runs on application startup.
  - Automatically triggers snapshot generation if > 24 hours have elapsed since the last backup.
  - Enforces rolling 7-day retention policy to prevent local disk exhaustion.
- **Disaster Recovery Restoration Algorithm**:
  - Reads `.dhanbackup` file, verifies manifest integrity, and upserts relational entities in strict foreign-key dependency order.
  - Unpacks report attachments into `uploads/reports/{tenant_id}/`.
  - Enables 1-click restore during PC migration or OS reinstallation with zero data loss.

### 3.6 Progressive Web App (PWA) & Responsive Mobile/Tablet Architecture
- **Web App Manifest (`/ui/manifest.json`)**: Configures application name, theme color (`#2563eb`), display mode (`standalone`), and high-res vector icons (192px and 512px).
- **Service Worker (`/ui/sw.js`)**: Caches static app shell, stylesheets, FontAwesome assets, and UI components for fast local launching.
- **Responsive Drawer**: Sliding drawer navigation with darkened backdrop for smartphones and tablets (`@media(max-width: 640px)`).

### 3.7 Client Theming Engine
- Powered by dynamic CSS custom properties (`:root`, `[data-theme]`).
- Supports 3 tailored healthcare palettes:
  - **Ocean Blue** (`ocean`): Classic sapphire medical blue (`#2563eb`).
  - **Emerald Health** (`emerald`): Refined surgical teal and botanical green (`#0d9488`).
  - **Royal Indigo** (`indigo`): Modern specialty hospital indigo-violet (`#4f46e5`).
- Real-time live switching from both the Login screen and the Topbar, persisted in `localStorage('dhan_theme')`.

---

## 4. Technology Stack

| Layer | Component | Version / Technology |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI | `>= 0.100.0` |
| **ASGI Server** | Uvicorn | `>= 0.22.0` |
| **ORM & Database Access** | SQLAlchemy | `>= 2.0.0` |
| **Database Engines** | PostgreSQL (Primary) / SQLite (Test) | PostgreSQL 15+ / SQLite 3 |
| **Document Generation** | ReportLab | `>= 4.0.0` |
| **BiDi & Arabic Shaping** | `arabic-reshaper`, `python-bidi` | `>= 3.0.0`, `>= 0.6.0` |
| **Security & Cryptography** | `passlib[bcrypt]`, `cryptography` (Fernet) | `>= 1.7.4`, `>= 41.0.0` |
| **Desktop Wrapper** | PyWebView | `>= 6.2.1` |
| **Progressive Web App** | Service Worker, Web App Manifest | Modern W3C Standard |
| **Frontend Framework** | Vanilla HTML5, CSS3, ES6 JavaScript | Zero external node_modules |

---

## 5. Security & Compliance Architecture (HIPAA & DPDP Act 2023)

### 5.1 Comprehensive Audit Logging
- **Compliance Standard**: HIPAA Security Rule § 164.312(b) & India DPDP Act 2023.
- **Access Granted**: Accessible to `ADMIN`, `DOCTOR`, and `DOCTOR_ALL` roles.
- **Coverage**:
  - `AUTH`: Password and OTP logins, failed attempts, logouts, session timeouts.
  - `PATIENT`: Patient registrations, searches, history lookups.
  - `CONSULTATION`: Consultations started/completed, prescriptions printed.
  - `REPORTS`: Diagnostic report uploads, views, downloads, deletions.
  - `SYSTEM`: Database backup creations, downloads, and restorations.

### 5.2 Automatic Session Inactivity Timeout (15 Mins)
- Enforces automatic logoff after 15 minutes of user inactivity (HIPAA § 164.312(a)(2)(iii)).
- Includes 60-second interactive countdown warning dialog.

### 5.3 Database Field-Level Encryption
- AES-256 (Fernet) encryption at rest for patient PII and clinical notes.

### 5.4 HTTPS / TLS 1.3 & Security Headers
- HSTS (`Strict-Transport-Security`), CSP, X-Frame-Options DENY, and anti-MIME spoofing headers.
