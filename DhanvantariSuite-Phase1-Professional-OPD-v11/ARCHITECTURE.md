# Dhanvantari Clinic ERP — System Architecture & Design Specification

## 1. Architectural Overview

Dhanvantari Clinic ERP is built on a **Hexagonal Architecture (Ports and Adapters / Clean Architecture)** design pattern. It operates under a **Unified Engine Hybrid Deployment** model, allowing the identical codebase to run either as a **Multi-Tenant Cloud SaaS** or as a **Single-Tenant Local Desktop Application** (via PyWebView) without architectural branching.

```
+---------------------------------------------------------------------------------+
|                                 USER INTERFACES                                 |
|   +------------------------------------+   +--------------------------------+   |
|   |    Single-Page Web Application     |   |    PyWebView Desktop Shell     |   |
|   |  (HTML5 / Vanilla CSS3 / ES6 / RTL)|   |   (Local Native Window Host)   |   |
|   +------------------------------------+   +--------------------------------+   |
+---------------------------------------------------------------------------------+
                                       |
                                       v  HTTP / REST / JSON
+---------------------------------------------------------------------------------+
|                       ADAPTERS LAYER — DRIVING (INBOUND)                        |
|   FastAPI REST Routers:                                                         |
|   - router_auth (JWT, Bcrypt, OTP)        - router_queue (Live OPD, Check-in)   |
|   - router_patient (Demographics, Search) - router_consultation (Clinical, Rx)  |
|   - router_billing (Invoices, Receipts)   - router_admin (Clinic Config, Users) |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
|                                APPLICATION SERVICES                             |
|   - AuthService          (Password verification, OTP lifecycle, JWT generation) |
|   - QueueService         (Token generation, OPD state machine, live metrics)    |
|   - ConsultationService  (Clinical encounters, vitals, Rx management)          |
|   - BillingService       (Invoice calculation, payment receipting)              |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
|                                   DOMAIN CORE                                   |
|   - Domain Entities: Patient, Appointment, Consultation, Vitals, Invoice, User  |
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
+---------------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

### 2.1 Hexagonal Layering & Dependency Inversion
- **Domain Core (`src/domain/`)**: Contains pure business entities and port definitions. The core has zero external framework dependencies (no FastAPI, no SQLAlchemy, no ReportLab).
- **Application Services (`src/services/`)**: Orchestrates business workflows (e.g., verifying an OTP, calculating BMI, moving appointments through the OPD pipeline).
- **Adapters (`src/adapters/`)**:
  - **Inbound Adapters (`src/adapters/api/`)**: FastAPI endpoints translate incoming HTTP requests into service invocations.
  - **Outbound Adapters (`src/adapters/db/`, `src/adapters/docgen/`)**: Implement domain repository ports using SQLAlchemy ORM and document generation ports using ReportLab.

### 2.2 Multi-Tenant Data Isolation Strategy
- All relational tables incorporate `tenant_id` and `branch_id` columns.
- High-performance logical data isolation is achieved using composite indices:
  ```sql
  CREATE INDEX idx_patients_tenant_branch ON patients(tenant_id, branch_id);
  CREATE INDEX idx_appointments_tenant_branch_date ON appointments(tenant_id, branch_id, appointment_date);
  ```
- In multi-tenant cloud mode, the `get_tenant_context` dependency extracts `tenant_id` and `branch_id` from the validated JWT token and automatically scopes all database queries.
- In standalone desktop mode, the system injects a default tenant identity (`local-clinic`) transparently.

---

## 3. Subsystem Architecture

### 3.1 Authentication & Credential Provider
The authentication system supports dual credential validation paths:

```
                      +-----------------------------+
                      |     Client Authentication   |
                      +-----------------------------+
                                     |
                    +----------------+---------------+
                    |                                |
         [ Password Mode ]                    [ OTP Mode ]
                    |                                |
                    v                                v
        +-----------------------+        +-----------------------+
        | Bcrypt / Passlib Hash |        | OTP Service / Cache   |
        | Verification against  |        | - 6-Digit Crypto Code |
        | users table           |        | - 5-Min TTL Expiry    |
        |                       |        | - 3 Max Retry Guard   |
        +-----------------------+        +-----------------------+
                    |                                |
                    +----------------+---------------+
                                     |
                                     v
                       +---------------------------+
                       | Issue Stateless JWT Token |
                       | (Identity, Role, Tenant)  |
                       +---------------------------+
```

- **Password Authentication**: Validates salted bcrypt password hashes.
- **OTP Authentication**:
  - Request endpoint (`POST /api/auth/otp/request`) looks up user by username or 10-digit mobile number.
  - Generates a cryptographically random 6-digit OTP stored with creation timestamp, expiration (300 seconds), and attempt counter.
  - Verify endpoint (`POST /api/auth/otp/verify`) checks code validity, enforces a maximum of 3 invalid attempts before invalidating the token, and issues standard JWT tokens.
  - Architecture is designed for SMS gateway integration (e.g., Twilio, Gupshup, Fast2SMS) via an outbound messaging port.

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

#### State Synchronization Mechanics
- **Persistent Footfall Tracking**: `list_queue` includes all appointment states (`SCHEDULED`, `CHECKED_IN`, `IN_CONSULTATION`, `COMPLETED`). Completing an appointment never deletes or hides it from the day's record.
- **5-Metric KPI Dashboard**:
  - `Today's Patients` = $\sum(\text{Scheduled} + \text{Checked In} + \text{In Consultation} + \text{Completed})$
  - `Checked In` = Count of patients with status `CHECKED_IN`
  - `In Consultation` = Count of patients with status `IN_CONSULTATION`
  - `Completed Patients` = Count of patients with status `COMPLETED`
  - `Scheduled` = Count of patients with status `SCHEDULED`
- **Zero-Overhead Live Polling**: Frontend polls `GET /api/queue/live/details` every 3000ms. In lightweight clinic and LAN environments, this eliminates WebSocket connection state overhead and reconnect fragility while ensuring instantaneous UI updates across receptionists and doctors.

### 3.3 Multilingual & Right-to-Left (RTL) Architecture

#### UI Localization Engine
- Pure vanilla client-side localization system (`i18n` dictionary).
- Switches interface strings dynamically without page reload.
- Automatically handles bidirectional layout transitions:
  - English, Marathi, Hindi: Left-to-Right (`dir="ltr"`).
  - Arabic: Right-to-Left (`dir="rtl"`), flipping navigation, tables, and form alignment.

#### Multilingual PDF Generation Engine (`DocGenPort`)
- Built on Python ReportLab with Unicode TrueType typography:
  - **Devanagari Font**: Registered from Windows font catalog (`Nirmala.ttc`, subfont 0) to natively render Marathi (`mr`) and Hindi (`hi`) conjunct characters and diacritics.
  - **Arabic Font & Shaping**: Registered from `arial.ttf`. Arabic text undergoes contextual glyph shaping via `arabic-reshaper` and bidirectional visual reordering via `python-bidi` before rendering into ReportLab canvases.
- **Pharmaceutical Safety Rule**:
  - **Medicine names (`medicine_name`) are strictly preserved in English / Latin brand names**.
  - Clinical section titles, instructions, vitals labels, duration units, and frequency indicators are fully translated into the selected target language.

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
| **Security & Cryptography** | `passlib[bcrypt]`, `python-jose` | `>= 1.7.4`, `>= 3.3.0` |
| **Desktop Wrapper** | PyWebView | `>= 6.2.1` |
| **Frontend Framework** | Vanilla HTML5, CSS3, ES6 JavaScript | Zero external node_modules |

---

## 5. Security & Compliance Architecture (HIPAA & DPDP Act 2023)

### 5.1 Comprehensive Audit Logging (Access, Read, Write, Export, Print)
- **Compliance Standard**: HIPAA Security Rule § 164.312(b) & India DPDP Act 2023.
- **Audit Domain Model**: `AuditLog` records immutable logs persisting `tenant_id`, `branch_id`, `user_id`, `user_role`, `action`, `module`, `record_id`, `ip_address`, `timestamp`, and `summary`.
- **Full Operational Coverage**:
  - **Access**: `LOGIN_PASSWORD_SUCCESS`, `LOGIN_OTP_SUCCESS`, `LOGIN_FAILED`, `OTP_VERIFY_FAILED`, `LOGOUT`, `SESSION_TIMEOUT`.
  - **Read**: `READ_PATIENT`, `SEARCH_PATIENTS`, `READ_CONSULTATION`, `READ_CLINICAL_HISTORY`, `READ_INVOICE_LIST`.
  - **Write**: `CREATE_PATIENT`, `START_VISIT`, `BOOK_APPOINTMENT`, `CHECK_IN_PATIENT`, `START_CONSULTATION`, `COMPLETE_CONSULTATION`, `RECORD_VITALS`, `CREATE_INVOICE`, `COLLECT_PAYMENT`, `UPDATE_USER_PERMISSIONS`.
  - **Export & Print**: `PRINT_PRESCRIPTION`, `PRINT_INVOICE_RECEIPT`.
- **Admin Audit Trail Dashboard**: Restricted to `ADMIN` role via `GET /api/audit-logs` with module, action, date range, and user filters.

### 5.2 Automatic Session Inactivity Timeout (15 Mins)
- **Compliance Standard**: HIPAA § 164.312(a)(2)(iii) (Automatic Logoff).
- **Client Inactivity Tracker**: Monitored via throttled event listeners (`mousemove`, `mousedown`, `keydown`, `touchstart`, `scroll`).
- **Grace Warning**: Displays an interactive modal dialog at 14 minutes with real-time second countdown and a "Stay Signed In" button.
- **Forced Termination**: Automatically purges client JWT tokens at 15 minutes of inactivity, dispatches `POST /api/auth/logout?reason=inactivity_timeout` to record `SESSION_TIMEOUT` in the audit log, and renders a secure session lock alert banner on the login screen.

### 5.3 Database Field-Level Encryption (PII & Sensitive Clinical Notes)
- **Compliance Standard**: HIPAA § 164.312(a)(2)(iv) (Encryption and Decryption) & DPDP Act Data Fiduciary requirements.
- **Symmetric Cipher**: AES-256 (Fernet) field-level encryption integrated via SQLAlchemy `EncryptedText` TypeDecorator.
- **Protected Fields at Rest**:
  - Patient Demographics & PII: `address`, `alternate_number`, `email`, `allergies`, `medical_notes`, `emergency_contact`.
  - Clinical Records: `symptoms`, `diagnosis`, `prescription_json`, `notes` in `consultations`, and `notes` in `appointments`.
- **Zero-Friction In-Memory Decryption**: Transparently decrypts on model load for authenticated users and safely falls back for legacy unencrypted database rows.

### 5.4 HTTPS / TLS 1.3 & Security Response Headers
- **Compliance Standard**: HIPAA § 164.312(e)(1) (Transmission Security).
- **HTTP Response Security Headers**:
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (enforces HTTPS)
  - `X-Frame-Options: DENY` (anti-clickjacking)
  - `X-Content-Type-Options: nosniff` (anti-MIME type spoofing)
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
  - `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; font-src 'self' data: https://cdnjs.cloudflare.com; connect-src 'self'; frame-ancestors 'none';`
- **TLS 1.3 / 1.2 Enforcement**: Programmatic certificate generation via `generate_ssl_certs.py` and HTTPS runner `start_server_https.bat` / `python src/server.py --https`.
