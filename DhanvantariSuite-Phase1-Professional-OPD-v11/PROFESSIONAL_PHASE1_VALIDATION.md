# DhanvantariSuite Phase 1 — Professional OPD Validation

This build is based on the user's tested Smart Simple UI v8 project and is intended to support both small clinics and multi-doctor hospitals without creating separate UIs.

## Roles
- Admin: users, clinic configuration, monitoring, billing visibility, reports.
- Doctor: own patients, consultation, prescription, optional vitals, optional payment collection.
- Receptionist: patient registration, appointments, check-in, queue operations, optional vitals, optional payment collection.
- No Nurse role, no separate Billing role, no Super Doctor role in Phase 1.

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
- Check-in changes the visit to Waiting.
- Doctor sees only patients assigned to that doctor.
- When a waiting patient is checked in, the doctor's dashboard detects it automatically and opens the patient if the doctor is free.
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
Reception, Doctor and Admin refresh today's OPD data automatically. Search/filter state is preserved during refresh. When a doctor starts consultation or completes consultation, the same central visit status is visible to other authorized dashboards.

## Today's OPD
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

## Consulting Doctor vs Referred By
These are independent concepts.
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
- Doctor cannot open another doctor's patient for clinical editing.
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
