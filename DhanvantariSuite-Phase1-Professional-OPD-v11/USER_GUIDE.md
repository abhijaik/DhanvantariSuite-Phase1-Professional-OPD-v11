# Dhanvantari Clinic ERP — Comprehensive User Guide

Welcome to the **Dhanvantari Clinic ERP (Professional OPD Edition)**. This user guide outlines daily clinic workflows, patient diagnostic reports management, doctor analytics, periodic database backups, multilingual prescriptions, and mobile/tablet PWA capabilities.

---

## 1. Getting Started & Multilingual Interface

### Accessing the System
- **Web Browser (LAN / Cloud)**: Open Chrome, Edge, or Safari and navigate to `http://<server-ip>:8000/ui/` (or `http://127.0.0.1:8000/ui/` locally).
- **Desktop Application**: Double-click `start_client.bat` to launch the native PyWebView desktop window.
- **Mobile / Tablet (PWA)**: Navigate to the clinic URL in Chrome (Android) or Safari (iOS) and tap **Install App** or **Add to Home Screen**.

### Multilingual Support & RTL
The interface supports dynamic language switching with zero page reloads:
- **Available Languages**:
  - **English (EN)**
  - **मराठी (MR)** — Marathi
  - **हिंदी (HI)** — Hindi
  - **العربية (AR)** — Arabic (Native Right-to-Left / RTL layout)
- **Changing Language**: Use the dropdown on the top-right of the login screen or in the top navigation bar at any time.

---

## 2. Secure Login: Password or OTP

Users can authenticate using either their account password or a one-time password (OTP).

### Option A: Password Login
1. Select the **Password** tab.
2. Enter your **Username** (e.g., `doctor_user`, `receptionist_user`, or `admin_user`).
3. Enter your **Password** and click **Sign In**.

### Option B: OTP Login
1. Select the **OTP Login** tab.
2. Enter your registered **Username** or **10-digit Mobile Number**.
3. Click **Send OTP** (generates a 6-digit code valid for 5 minutes).
4. Enter the code in the OTP field and click **Verify & Sign In**.

---

## 3. User Roles & Access Matrix

| Role | OPD Queue Access | Patient Registration | Start Consultation | View Doctor Reports | Audit Logs | Backup & Restore |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Admin** | View All | Yes | No (Read-Only) | Yes | Full View | Yes |
| **Receptionist** | View All | Yes | No | No | No | No |
| **Doctor** | Own Assigned Queue | Yes | Yes (Full Rx) | Yes | Full View | Yes |
| **Doctor_All** | View & Manage All | Yes | Yes (Any Patient) | Yes | Full View | Yes |

---

## 4. Today's OPD Dashboard & Real-Time Synchronization

The **Today / OPD** dashboard serves as the central operational hub:
- **Live 5-Metric KPI Summary**:
  - `Today's Patients`: Total patient visits scheduled or recorded for today.
  - `Checked In`: Patients currently waiting in the clinic lobby.
  - `In Consultation`: Patients currently inside the doctor's cabin.
  - `Completed Patients`: Patients whose consultations have concluded today.
  - `Scheduled`: Patients booked for today who have not yet checked in.
- **3-Second Auto-Sync**: Updates occur automatically without manual page refreshing.
- **Doctor Direct Check-In**: Doctors can check in arriving scheduled patients directly from their dashboard.

---

## 5. Front Desk Workflows (Receptionist & Admin)

### A. New Patient Registration & OPD Visit
1. Click **+ New Patient** on the top action bar.
2. Fill in the demographics: Name, Age, Gender, and 10-digit Mobile Number.
3. Select the **Consulting Doctor** and optional referral information.
4. Click **Save Patient**. When the patient arrives in the waiting area, click **Check-in** to issue a token.

### B. Finding Existing Patients & Follow-Up Visits
1. Click **Find Patient** and search by mobile number, name, or Patient ID.
2. Click **Start Visit** to register today's encounter while preserving past medical history.

---

## 6. Doctor Consultation Workflow

### A. Opening Consultation
1. Navigate to **Today / OPD**.
2. Click on any patient with status **Waiting / Checked In** to open the consultation workspace.

### B. Clinical Documentation
1. **Vitals Recording**: Review or record Blood Pressure, Pulse, Temperature, Weight, Height, and SpO2 (BMI calculates automatically).
2. **Patient History & Past Reports**: Click **History** to view previous consultation prescriptions or **Reports** to inspect lab/scan documents.
3. **Prescription (Rx)**: Input medicine names, dosage, frequency (e.g., 1-0-1), food relationship, duration, and patient instructions.
4. **Follow-Up Scheduling**: Pick a recommended follow-up date.
5. Click **Complete Consultation** to finalize the clinical encounter.

---

## 7. Multilingual Prescription Generation

Prescriptions can be printed or exported as high-fidelity PDFs:
1. Click **Print Prescription** on the consultation screen or from the OPD queue.
2. Choose your preferred language: **English**, **मराठी**, **हिंदी**, or **العربية**.
3. **Pharmaceutical Safety Guard**: Medicine brand names strictly remain in English/Latin script to prevent dispensing errors, while all clinical findings, directions, vitals, and instructions are localized.

---

## 8. Patient Diagnostic & Lab Reports

Dhanvantari Clinic ERP provides centralized storage for diagnostic reports directly linked to patient history.

### A. Accessing Reports
- In **Doctor Consultation**: Click the **Reports** or **+ Upload Report** button on the patient banner.
- In **Today's Queue** or **Patient Directory**: Click **History** on any patient row, then select **2. Diagnostic & Lab Reports**.

### B. Upload Methods (4 Options)
Click **+ Upload / Link Report** to open the upload modal:
1. **File Upload**: Choose a PDF, JPG, PNG, WEBP, or DOCX document (up to 25MB).
2. **Google Drive Link**: Paste any shareable Google Drive link (e.g. `https://drive.google.com/file/d/.../view`). The system automatically converts it into an embedded preview.
3. **Camera / Mobile Scan**: On smartphones or tablets, tapping this option directly launches the device camera to photograph paper lab reports.
4. **Cloud / Web Link**: Attach external URLs from hospital portals or Dropbox.

### C. In-App Preview & Downloads
- Click **View** on any report card to open an instant in-modal preview (interactive PDF viewer, full-screen image viewer, or Google Drive embed).
- Click **Download** to save a copy locally.

---

## 9. Doctor Reports & Clinical Analytics

Clinicians can monitor practice trends via the dedicated **Reports** tab (available to `Doctor` and `Doctor_All` roles):
1. **Date Filtering**: Select custom date ranges (Today, This Week, This Month, or custom date ranges).
2. **Report Categories**:
   - **OPD Summary**: Consultation counts by visit type (General, Follow-up, Emergency, Specialist).
   - **Follow-Up Tracker**: Categorizes patients whose follow-ups are upcoming, due today, or overdue with 1-click WhatsApp/Call links.
   - **Top Diagnoses & Symptoms**: Disease frequency ranking to identify prevalent local conditions.
   - **Most Prescribed Medicines**: Identifies top drugs and frequency.
   - **Revenue Breakdown**: Financial collections categorized by payment mode (Cash, UPI, Card).
   - **Referrals**: Patient volume attributed to referring doctors or facilities.
3. **Export to CSV**: Click **Export CSV** on any report to download structured data for Excel or clinical audits.

---

## 10. Audit Trail & Compliance

To meet HIPAA § 164.312(b) and India DPDP Act 2023 technical safeguards:
- **Access**: Available to **Admin** and **Doctor** roles under the **Audit Trail** tab.
- **Log Verification**: Tracks all logins, logouts, patient views, prescription prints, report uploads, and database backups.
- **Filter**: Filter by Module (`AUTH`, `PATIENT`, `CONSULTATION`, `REPORTS`, `SYSTEM`), action type, date range, or staff username.

---

## 11. WhatsApp-Style Periodic Database Backup & Restore

Protect clinic data against hardware failures, PC crashes, or OS reinstallation.

### A. Automated Periodic Daily Backup
- When the clinic system runs, it automatically verifies if 24 hours have elapsed since the last backup.
- It automatically creates a snapshot archive (`.dhanbackup`) in `backups/{tenant_id}/` and maintains a rolling 7-day retention.

### B. Manual Backup ("Backup Now")
1. In the sidebar under your profile, click **DB Backup** (or go to **Admin -> Database Backup**).
2. Click **Backup Now**.
3. A compressed `.dhanbackup` archive is generated containing all database records and uploaded report files.
4. Click **Download** to copy the archive to a USB flash drive or cloud storage.

### C. Reinstalling / Disaster Recovery ("Restore from File")
If moving to a new computer or reinstalling Dhanvantari:
1. Open the clean installation of Dhanvantari Clinic ERP.
2. Click **DB Backup** -> **Restore from File**.
3. Select your `.dhanbackup` file and click **Restore Data**.
4. The system validates the archive, restores all patient records, consultations, invoices, and diagnostic files, and reloads the application.

---

## 12. Customizing Color Themes

Users can choose from 3 professional healthcare color themes:
- 🌊 **Ocean Blue** *(Default)*: Trustworthy medical sapphire blue.
- 🌿 **Emerald Health**: Fresh botanical surgical teal and mint green (reduces eye strain).
- 👑 **Royal Indigo**: Deep specialty hospital indigo-violet.

**How to switch themes**:
- **On the Login Screen**: Select your preferred theme from the dropdown before signing in.
- **Inside the Application**: Click the theme dropdown in the top navigation bar for instant live preview.

---

## 13. Mobile & Tablet Usage (PWA Installation)

Dhanvantari Clinic ERP is a fully responsive **Progressive Web App (PWA)**:
- **Installation**:
  - **Chrome (Android / Desktop)**: Tap the **Install App** button on the topbar or select *Install Dhanvantari* from the browser menu.
  - **Safari (iOS / iPadOS)**: Tap the *Share* button and select *Add to Home Screen*.
- **Mobile Navigation**: Use the hamburger menu (`fa-bars`) to open the sliding navigation drawer.
- **Camera Scanning**: Take direct photos of physical prescription slips or lab sheets using the mobile camera upload option.

---

## 14. Troubleshooting & FAQ

- **Q: How do I recover data after formatting my computer?**
  - *A: Install the application, go to DB Backup -> Restore from File, and upload your latest `.dhanbackup` file.*
- **Q: Why are medicine brand names in English even when Marathi/Hindi/Arabic is selected?**
  - *A: This is an intentional pharmaceutical safety standard to eliminate dispensing errors at pharmacies while keeping patient instructions fully localized.*
- **Q: Does Google Drive preview require logging into Google?**
  - *A: As long as the Google Drive link has sharing set to "Anyone with the link can view", it renders inside the modal without requiring user login.*
