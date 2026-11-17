# Professional OPD Release Changelog & Implementation Notes

## Version 11.2 (Current Release)

### 1. Patient Diagnostic & Lab Reports Subsystem
- **Domain & Persistence**:
  - Added `PatientReport` domain model and `ReportSourceType` enum (`FILE_UPLOAD`, `GOOGLE_DRIVE`, `CAMERA_SCAN`, `EXTERNAL_URL`).
  - Created `PatientReportORM` in `src/adapters/db/orm_models.py` with composite indexing on `(tenant_id, patient_id)` and `(tenant_id, branch_id)`.
  - Added `router_patient_reports.py` supporting multipart file uploads, Google Drive URL extraction, listing, streaming download, and deletion.
- **Frontend & UX**:
  - Upgraded Patient History modal in `index.html` with dual tabs: **1. Consultations History** and **2. Diagnostic & Lab Reports**.
  - Built multi-source upload modal supporting direct PDF/image files (up to 25MB), Google Drive links with auto-preview URL generation, native mobile camera capture (`capture="environment"`), and cloud URLs.
  - Implemented in-modal interactive PDF viewer, full-screen image viewer, Google Drive iframe embed, and direct downloads.
  - Added 1-click **Reports** and **+ Upload Report** shortcuts in Doctor Consultation workspace.

### 2. Doctor Clinical Analytics & Reporting Suite
- **API & Analytics Engine**:
  - Added `router_reports.py` restricted to `DOCTOR` and `DOCTOR_ALL` roles.
  - Implemented 6 core clinical report categories:
    - **OPD Summary**: Breakdown by visit type (General, Follow-up, Emergency, Specialist).
    - **Follow-Up Tracker**: Categorization into Upcoming, Due Today, and Overdue with direct WhatsApp/Call links.
    - **Top Diagnoses & Symptoms**: Disease frequency ranking for epidemiological tracking.
    - **Most Prescribed Medicines**: Frequency counts of prescribed brand medications.
    - **Revenue Summary**: Invoicing volume, billed amounts, collected amounts, and pending dues by payment mode.
    - **Referral Analysis**: Patient counts by referring physician or organization.
- **Frontend & Export**:
  - Added top-level **Reports** navigation tab with date range filters (Today, This Week, This Month, Custom).
  - Built RFC 4180 compliant client-side CSV streaming export for offline spreadsheet analysis.

### 3. WhatsApp-Style Periodic Database Backup & Disaster Recovery
- **Backup Engine (`backup_service.py`)**:
  - Implemented `.dhanbackup` portable compressed ZIP archive specification.
  - Bundles `manifest.json` (metadata & counts), `database.json` (complete relational dump across all 12 ORM models), and `reports/` (all physical uploaded patient files).
  - Implemented rolling 7-day retention for automatic backups.
- **API Endpoints (`router_backup.py`)**:
  - `POST /api/backup/create`: On-demand manual backup creation.
  - `GET /api/backup/list`: Lists existing backups with file sizes and timestamps.
  - `GET /api/backup/download/{filename}`: Secure authenticated backup file download.
  - `POST /api/backup/restore`: Complete disaster recovery restoration with manifest validation and file extraction.
  - `POST /api/backup/auto-check`: Automated 24-hour background backup scheduler triggered on startup.
- **UI Integration**:
  - Added **Database Backup & Disaster Recovery** card in Admin settings and persistent **DB Backup** action button in Doctor sidebar profile.
  - 1-click **Restore from File** modal for seamless PC migration and reinstallation.

### 4. Progressive Web App (PWA) & Mobile/Tablet Support
- Created Web App Manifest (`/ui/manifest.json`) and Service Worker (`/ui/sw.js`) with offline app shell caching.
- Generated high-resolution vector application icons (`icon-192.png` and `icon-512.png`).
- Added responsive sliding navigation drawer with darkened backdrop for smartphones and tablets (`@media(max-width: 640px)`).
- Added browser install prompt banner (`Install App`).

### 5. 3 Professional Healthcare Color Themes
- Built dynamic CSS variable switching system via `data-theme` attribute:
  - 🌊 **Ocean Blue** (`ocean`): Classic sapphire medical blue (`#2563eb`).
  - 🌿 **Emerald Health** (`emerald`): Refined surgical teal and botanical green (`#0d9488`).
  - 👑 **Royal Indigo** (`indigo`): Modern specialty hospital indigo-violet (`#4f46e5`).
- Placed interactive theme selectors on **both the Login/Home screen and the Main Application Topbar**.
- Persists user selection in `localStorage('dhan_theme')` and synchronizes mobile browser theme color.

### 6. HIPAA & DPDP Act Audit Trail Expansion
- Updated `router_audit.py` to grant `DOCTOR` and `DOCTOR_ALL` roles permission to access the **Audit Trail** alongside `ADMIN`.
- Integrated audit logging for all report operations (`UPLOAD_PATIENT_REPORT`, `READ_PATIENT_REPORTS`, `VIEW_PATIENT_REPORT`, `DELETE_PATIENT_REPORT`) and backup operations (`CREATE_DATABASE_BACKUP`, `DOWNLOAD_DATABASE_BACKUP`, `RESTORE_DATABASE_BACKUP`).

---

## Version 11.1
- **Live Dashboard Count Synchronization**:
  - Fixed database query in `SQLAlchemyAppointmentRepository.list_queue` to include `COMPLETED` visits, ensuring today's total patient footfall counts persist accurately without dropping upon consultation completion.
  - Added a 5-stat KPI dashboard bar: **Today's Patients**, **Checked In**, **In Consultation**, **Completed Patients**, and **Scheduled**.
  - Repaired and optimized the client-side 3-second live polling loop: Receptionist and Doctor views now synchronize automatically at runtime without manual page reloads.
  - Enabled direct Doctor check-in for scheduled patients assigned to them.
  - Completed patients now display prominently in the queue with a green **Completed** status badge, a 1-click **Collect Payment** action button for cashier/receptionist, and a **Prescription** view button.

- **Multilingual Support & RTL Integration**:
  - UI language switcher supporting **English (EN)**, **मराठी (MR)**, **हिंदी (HI)**, and **العربية (AR)** across both the login screen and the main application header.
  - Automatic Right-to-Left (RTL) layout switching via `dir="rtl"` when Arabic is selected.
  - Multilingual PDF prescription generator with Unicode font support (`Nirmala.ttc` for Devanagari script, `arial.ttf` with `arabic-reshaper` and `python-bidi` for Arabic).
  - Prescriptions can be printed in the patient's language of choice on demand.
  - **Drug Safety Rule**: Medicine brand names strictly remain in English/Latin script to prevent dispensing errors, while all clinical findings, directions, vitals, and instructions are localized.

- **Dual Authentication (Password / OTP)**:
  - Added login selection tabs allowing users to choose between **Password Login** and **OTP Login**.
  - Added backend endpoints `POST /api/auth/otp/request` and `POST /api/auth/otp/verify`.
  - Supports user lookup by username or registered 10-digit mobile number (`find_by_username_or_mobile`).
  - 6-digit OTP generation with 5-minute time-to-live (TTL) and 3-attempt brute-force protection.
  - Seamless issuance of standard JWT bearer tokens upon successful OTP verification.

---

## Version 11.0 (Baseline)
- Reception/Admin New Patient creates a visit in Scheduled/Booked state; it does NOT start consultation immediately.
- Reception must click Check-in when the patient arrives in the OPD lobby.
- Check-in transitions centralized visit status to Waiting / Checked In and places the patient in the assigned doctor's active queue with a daily token.
- Doctor New Patient may still open consultation directly for a single-doctor workflow.
- Multi-doctor workflow requires Consulting Doctor assignment and queue/token behavior.
- Today's OPD remains the shared central source of truth across Reception, Doctor, and Admin.
- Updated typography to a clean Aptos/Segoe UI system font stack.
