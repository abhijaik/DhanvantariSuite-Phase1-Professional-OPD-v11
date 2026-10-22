# DhanvantariSuite Phase 1 — Professional OPD Validation

This build is based on the user's tested Smart Simple UI v8 project and is intended to support both small clinics and multi-doctor hospitals without creating separate UIs.

## Roles
- **Admin**: users, clinic configuration, monitoring, billing visibility, reports.
- **Doctor**: own patients, consultation, prescription, direct check-in, optional vitals, optional payment collection.
- **Doctor_All**: super-user clinician access across all clinic doctors.
- **Receptionist**: patient registration, appointments, check-in, queue operations, optional vitals, optional payment collection.
- No Nurse role, no separate Billing role in Phase 1.

## Authentication & Access
- **Dual Login**: Users can sign in using either account password or 6-digit OTP sent to their username/mobile.
- **OTP Security**: 5-minute validity window with a 3-attempt brute-force protection limit.
- **Multilingual Support**: Supports English, Marathi (मराठी), Hindi (हिंदी), and Arabic (العربية).
- **RTL Support**: Selecting Arabic automatically switches the entire layout to Right-to-Left (RTL).

## Clinic behavior
### Single active doctor
- No OPD token.
- Doctor registration can go directly to consultation.
- Reception registration creates an arrival/visit; doctor opens it from Today's OPD.
- Existing patient: Find Patient → Start Visit → previous history remains unchanged.

### Multiple active doctors
- Reception/Admin selects the Consulting Doctor where required.
- Token is generated for OPD visits managed through reception/admin.
- Patient appears in Today's OPD as Scheduled before arrival.
- Check-in changes the visit to Waiting / Checked In.
- Doctor sees only patients assigned to that doctor (Doctor_All sees all).
- When a waiting patient is checked in, the doctor's dashboard detects it automatically.
- If doctor is already consulting, the current consultation is never replaced; the next patient remains Waiting.

## Central visit status
One appointment/visit status is the source of truth for every dashboard:
- Scheduled
- Waiting (stored as CHECKED_IN or IN_QUEUE depending on clinic workflow)
- In Consultation
- Consultation Completed
- Cancelled

Payment status remains separate:
- Pending
- Partial
- Paid
- Refunded

## Dashboard synchronization
Reception, Doctor and Admin refresh today's OPD data automatically (3-second polling cadence). Search/filter state is preserved during refresh. When a doctor starts consultation or completes consultation, the same central visit status is visible to other authorized dashboards. Completed visits remain in the daily encounter queue with persistent total counts, a green Completed badge, and quick actions for payment collection and prescription viewing.

## Today's OPD & 5-Stat KPI Summary
- Live 5-metric KPI summary: **Today's Patients**, **Checked In**, **In Consultation**, **Completed Patients**, and **Scheduled**.
- Neutral heading: "Today's OPD"; no hard-coded single-doctor message.
- Doctor login: "Your patients today" and only assigned patients.
- Reception/Admin in multi-doctor setup: all doctors with a doctor filter.
- Search: patient name, mobile, patient ID, token, visit type, consultation type, doctor, status, referral source.

## Patient and follow-up
- Duplicate mobile detection prevents duplicate patient profiles.
- Existing patient workflow creates a new visit, never overwrites historical consultations.
- Follow-up screen shows previous history where the role is authorized.
- Vitals are available during new visit and follow-up.

## Vitals
Vitals can be recorded by Doctor or Receptionist according to Admin configuration:
- Blood pressure
- Weight
- Height
- BMI (automatic)
- Temperature
- Pulse
- SpO2
- Respiratory rate

Vitals are attached to the visit, include recorder information/time, and are automatically visible in the doctor's consultation.

## Multilingual Prescriptions
- Supports generation in English, Marathi, Hindi, and Arabic.
- **Drug Safety Rule**: Medicine brand names are strictly kept in English/Latin script to prevent pharmacy dispensing errors.
- Clinical headers, instructions, dosage, food relations, and follow-up advice are translated to the selected language.
- TrueType Unicode fonts (Devanagari for MR/HI, Arabic with bidirectional shaping for AR) guarantee crisp, compliant rendering.

## Consulting Doctor vs Referred By
These are independent concepts:
- Consulting Doctor: the internal doctor who will treat the patient and own the queue.
- Referred By: optional referral source (Doctor, Patient, Hospital/Clinic, Other) and name/source.
- Referral does not affect queue ownership.
- Follow-up can prefill prior referral information while allowing it to be changed for the new visit.

## Appointments
- Existing patient appointments are supported.
- New patient appointments by phone are supported without first requiring a completed registration.
- Future appointments remain Scheduled until arrival/check-in.
- Multi-doctor appointments receive a token; single-doctor clinics do not need OPD tokens.

## Billing
- Billing is a function, not a separate role.
- Doctor or Receptionist can collect payment when permitted; Admin has oversight.
- Consultation completion makes the visit eligible for billing.
- Payment records maintain payment mode, amount, status and collector context through the authenticated user.

## Authorization
- Clinical consultation creation/update is Doctor-only.
- Receptionist cannot start or edit a doctor consultation.
- Doctor cannot open another doctor's patient for clinical editing (except Doctor_All).
- Doctor can check in scheduled patients assigned to them directly.
- Vitals use both user permission and clinic recorder configuration.
- Payment collection uses user payment permission.
- Admin-only user management and vitals configuration.

## Professional UX principles
- Do not expose internal technical workflow terms when a simple action is sufficient.
- Prefer New Patient, Find Patient and Appointments as primary actions.
- System automatically decides doctor assignment, token/queue behavior and visit creation from clinic configuration and user role.
- Avoid duplicate data entry.
- Never replace an active consultation because another patient arrives.
- Every status transition must be visible consistently wherever the visit is displayed.
- Keep the underlying data model structured for future analytics/AI without exposing AI controls in Phase 1.

## Technical Safeguards (HIPAA § 164.312 & DPDP Act 2023 Compliance)
### 1. Comprehensive Audit Logging (Access, Read, Write, Export, Print)
- **Immutable Log Storage**: Persisted to `audit_logs` table (`user_id`, `user_role`, `action`, `module`, `record_id`, `ip_address`, `timestamp`, `summary`).
- **Access Events**: `LOGIN_PASSWORD_SUCCESS`, `LOGIN_OTP_SUCCESS`, `LOGIN_FAILED`, `OTP_VERIFY_FAILED`, `LOGOUT`, `SESSION_TIMEOUT`.
- **Read Events**: `READ_PATIENT`, `SEARCH_PATIENTS`, `READ_CONSULTATION`, `READ_CLINICAL_HISTORY`, `READ_INVOICE_LIST`.
- **Write Events**: `CREATE_PATIENT`, `START_VISIT`, `BOOK_APPOINTMENT`, `CHECK_IN_PATIENT`, `START_CONSULTATION`, `COMPLETE_CONSULTATION`, `RECORD_VITALS`, `CREATE_INVOICE`, `COLLECT_PAYMENT`, `UPDATE_USER_PERMISSIONS`.
- **Export & Print Events**: `PRINT_PRESCRIPTION` (localized Rx PDF), `PRINT_INVOICE_RECEIPT` (receipt PDF).
- **Admin Audit Trail UI**: Exclusive to Admin role via `GET /api/audit-logs` with module, action, user, and date range filters.

### 2. Automatic Session Inactivity Timeout (15 Mins)
- **15-Minute Timeout**: Client tracks user interaction (`mousemove`, `mousedown`, `keydown`, `touchstart`, `scroll`) throttled at 1000ms.
- **60-Second Warning**: At 14 minutes, displays modal with real-time countdown and "Stay Signed In" button.
- **Automated Termination**: At 15 minutes, terminates active session, clears storage, triggers `POST /api/auth/logout?reason=inactivity_timeout` (`SESSION_TIMEOUT` audit log), and presents a security lock notification banner on login.

### 3. Database Field-Level Encryption (PII & Sensitive Clinical Notes)
- **AES-256 (Fernet) Encryption**: Applied transparently via SQLAlchemy `EncryptedText` TypeDecorator.
- **Encrypted Patient PII**: `address`, `alternate_number`, `email`, `allergies`, `medical_notes`, `emergency_contact`.
- **Encrypted Clinical Notes**: `symptoms`, `diagnosis`, `prescription_json`, `notes` in `consultations` and `notes` in `appointments`.
- **Verification**: Direct raw SQL SELECT returns ciphertext tokens (`gAAAAA...`), while ORM queries decrypt values transparently in memory. Includes backward compatibility for legacy plaintext records.

### 4. HTTPS / TLS 1.3 & Security Response Headers (HSTS, CSP, X-Frame)
- **Security Response Headers**:
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
  - `X-Frame-Options: DENY` (anti-clickjacking)
  - `X-Content-Type-Options: nosniff` (anti-MIME sniffing)
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
  - `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; font-src 'self' data: https://cdnjs.cloudflare.com; connect-src 'self'; frame-ancestors 'none';`
- **TLS 1.3 / HTTPS Deployment**: Automated SAN certificate generation via `generate_ssl_certs.py` and HTTPS runner `start_server_https.bat` / `python src/server.py --https`.
