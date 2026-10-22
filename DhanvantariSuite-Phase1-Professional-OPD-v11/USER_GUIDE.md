# Dhanvantari Clinic ERP — Comprehensive User Guide

Welcome to the **Dhanvantari Clinic ERP (Professional OPD Edition)**. This user guide outlines the application workflows, multilingual capabilities, dual login mechanisms, real-time OPD dashboard synchronization, clinical consultation, and billing management.

---

## 1. Getting Started & Multilingual Interface

### Accessing the System
- **Web Browser**: Open your modern browser (Chrome, Edge, Firefox) and navigate to `http://127.0.0.1:8000/ui/`.
- **Desktop Application**: Double-click `start_client.bat` to launch the native PyWebView desktop container.

### Multilingual Support (English, Marathi, Hindi, Arabic)
The Dhanvantari Clinic ERP supports multi-language operation with dynamic script and layout switching:
- **Available Languages**:
  - **English (EN)**
  - **मराठी (MR)** — Marathi
  - **हिंदी (HI)** — Hindi
  - **العربية (AR)** — Arabic (Right-to-Left / RTL layout)
- **Changing Language**:
  - **Login Screen**: Click the language selector at the top-right corner to switch languages before logging in.
  - **Main Application**: Use the persistent language dropdown in the top navigation bar at any time. The entire user interface, status badges, table headers, and system alerts adapt immediately. When Arabic is selected, the layout automatically transforms to native Right-to-Left (RTL) mode.

---

## 2. Secure Login: Password or OTP

Users can authenticate using either their account password or a one-time password (OTP).

### Option A: Password Login
1. On the login screen, select the **Password Login** tab.
2. Enter your **Username** (e.g., `doctor_user`, `receptionist_user`, or `admin_user`).
3. Enter your **Password**.
4. Click **Sign In**.

### Option B: OTP Login (Mobile / Username)
1. Select the **OTP Login** tab.
2. Enter your registered **Username** or **10-digit Mobile Number**.
3. Click **Send OTP**.
   - A 6-digit secure code will be generated (valid for 5 minutes).
   - *In local/development mode, a notification banner displays the generated OTP for quick testing.*
4. Enter the 6-digit code in the **Enter 6-Digit OTP** field.
5. Click **Verify & Sign In**.
   - *Security Note: The system enforces a maximum of 3 failed verification attempts before the OTP expires.*
   - If needed, click **Resend OTP** after expiration.

---

## 3. User Roles & Access Matrix

| Role | OPD Queue Access | Patient Registration | Start Consultation | Collect Payments | System Settings & Users |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Admin** | View All | Yes | No (Read-Only) | Yes | Yes |
| **Receptionist** | View All | Yes | No | Yes | No |
| **Doctor** | Own Assigned Queue | Yes | Yes (Full Rx) | Optional (Configurable) | No |
| **Doctor_All** | View & Manage All | Yes | Yes (Any Patient) | Optional (Configurable) | No |

---

## 4. Today's OPD Dashboard & Real-Time Synchronization

The **Today / OPD** dashboard serves as the central operational hub for receptionists, nurses, and doctors.

### Live 5-Metric KPI Summary
The top metric bar provides real-time counts of today's patient pipeline:
1. **Today's Patients**: Total patient visits scheduled or recorded for today.
2. **Checked In**: Patients currently waiting in the clinic lobby for consultation.
3. **In Consultation**: Patients currently inside the doctor's cabin.
4. **Completed Patients**: Patients whose consultations have concluded today.
5. **Scheduled**: Patients booked for today who have not yet checked in.

### Runtime Synchronization (No Manual Refresh Required)
- Every action taken by a doctor (such as starting a consultation or completing a visit) or receptionist (such as patient registration, booking, or check-in) is automatically synchronized across all open screens within **3 seconds**.
- When a doctor completes a consultation:
  - The patient status instantly changes to **Completed**.
  - The **Completed Patients** counter increments immediately.
  - The patient remains in the Today's list with a green **Completed** badge, enabling receptionists to collect payments or print prescriptions.

---

## 5. Front Desk Workflows (Receptionist & Admin)

### A. New Patient Registration & OPD Visit
1. Click **+ New Patient** on the top action bar.
2. Fill in the patient demographics: Full Name, Age/DOB, Gender, and 10-digit Mobile Number.
3. In a multi-doctor clinic, select the **Consulting Doctor**.
4. (Optional) Record referral details (e.g., Referred by Doctor, Hospital, or Patient).
5. Click **Save Patient**.
   - In a multi-doctor clinic, an OPD visit is created with status **Scheduled**.
   - When the patient arrives in the waiting area, click **Check-in**. The status updates to **Waiting / Checked In** with a daily OPD token.

### B. Finding Existing Patients & Follow-Up Visits
1. Click **Find Patient**.
2. Search by mobile number, patient name, or Patient ID.
3. Click **Start Visit** to register today's encounter without duplicating the patient profile. Prior clinical history is preserved.

### C. Booking Appointments
1. Navigate to the **Appointments** tab or click **Book Appointment**.
2. Select the patient, assigned doctor, date, and appointment slot.
3. The visit appears in the **Scheduled** category and transitions to active queue once checked in.

---

## 6. Doctor Consultation Workflow

### A. Patient Queue & Check-In
1. Navigate to **Today / OPD**.
2. Filter is automatically scoped to your assigned patients (or all patients if role is `Doctor_All`).
3. If an arriving patient is in "Scheduled" status, click the **Check-in** button to move them into your active queue.
4. Click on any patient with status **Waiting / Checked In** to open the consultation workspace.

### B. Recording Clinical Notes
1. **Vitals Recording**: Review or record Blood Pressure, Pulse, Temperature, Weight, Height, SpO2, and Respiratory Rate (BMI calculates automatically).
2. **Chief Complaints & History**: Document presenting symptoms, duration, and clinical history.
3. **Examination & Diagnosis**: Input systemic findings and provisional/differential diagnosis.
4. **Prescription (Rx)**:
   - Search or input medicine brand names.
   - Enter dosage (e.g., 500mg, 1 tablet), frequency/timing (e.g., 1-0-1), food relationship (After Food / Before Food), and duration (e.g., 5 days).
   - Enter specific patient instructions.
5. **Advice & Follow-Up**: Enter general care advice, dietary precautions, and recommended follow-up date.

### C. Completing the Consultation
1. Click **Complete Consultation**.
2. The consultation is permanently saved, the visit status updates to **Completed**, and an invoice is automatically queued for billing.

---

## 7. Multilingual Prescription Generation

Prescriptions can be printed or exported as high-fidelity PDFs in multiple regional languages:

1. Click **Print Prescription** on the consultation screen or from the Today's OPD queue.
2. A **Print Prescription Language** dialog appears with available language choices:
   - **English Prescription**
   - **मराठी प्रिस्क्रिप्शन (Marathi)**
   - **हिंदी प्रिस्क्रिप्शन (Hindi)**
   - **وصفة طبية بالعربية (Arabic)**
3. **Pharmaceutical Safety Rule**:
   - **Medicine Names**: Maintained in **English/Latin script** (e.g., *Paracetamol 650mg*, *Amoxicillin 500mg*) to guarantee patient safety, eliminate pharmacy dispensing errors, and comply with drug naming regulations.
   - **Localized Content**: All section titles (Chief Complaints, Diagnosis, Rx, Dosage, Food Relation, Timing, Duration, Instructions, Vitals, Doctor Signature, Follow-up) are rendered in the selected language.
   - **Arabic RTL**: Renders right-to-left layout with contextual Arabic character shaping.
4. The generated PDF opens in a new tab ready for printing or saving.

---

## 8. Billing & Payment Collection

1. When a consultation is completed, it becomes immediately available in the **Billing** section.
2. Receptionists or authorized staff can locate the patient invoice either by:
   - Clicking **Collect Payment** directly on the patient's card in **Today's OPD**.
   - Navigating to the **Billing** tab and searching by Patient ID or Invoice number.
3. Choose the payment mode: **Cash**, **Card**, **UPI / QR Code**, or **Bank Transfer**.
4. Enter the amount collected (supports Full, Partial, or Pending payments).
5. Click **Record Payment**. An itemized receipt can be printed for the patient.

---

## 9. Troubleshooting & FAQ

- **Q: Why did today's patient count not drop after consultation?**
  - *A: This is by design. "Today's Patients" reflects the total daily footfall. Completed patients transition to the "Completed Patients" metric and display a green "Completed" badge.*
- **Q: Can a doctor check in a patient directly?**
  - *A: Yes. Doctors can check in any scheduled patient assigned to them directly from their Today's OPD view.*
- **Q: What happens if an OTP expires?**
  - *A: OTPs expire after 5 minutes. Click "Resend OTP" to generate a fresh verification code.*
- **Q: Are Marathi and Hindi fonts bundled?**
  - *A: Yes. The system leverages Devanagari typography (`Nirmala.ttc`) and TrueType Arabic fonts with automatic bidirectional shaping.*
