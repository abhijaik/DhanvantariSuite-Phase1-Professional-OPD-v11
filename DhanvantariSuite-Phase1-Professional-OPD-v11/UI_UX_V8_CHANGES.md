# Phase 1 Smart Simple UI v8 — Changes

## User-facing decisions
- Keep the clean existing visual design.
- Do not expose technical workflow terms unless needed.
- Main actions: **New Patient**, **Find Patient**, **Appointments**.
- Today's OPD now has its own search for name, mobile, patient ID, token, visit type, consultation type and doctor.

## Workflow corrections
1. Non-doctor users never see a dead-end “Doctor Consultation” authorization message. They return to Today/OPD.
2. Single-doctor clinic: no OPD token. Doctor can directly start consultation.
3. Receptionist + single doctor: patient can be checked in as ARRIVED; doctor can open the patient directly.
4. Multi-doctor clinic: receptionist/admin selects the doctor; token is generated and check-in puts patient in that doctor's queue.
5. Doctor auto-open watches both IN_QUEUE and CHECKED_IN, without interrupting an active consultation.
6. Existing-patient follow-up remains a separate new visit and preserves history.
7. New-patient appointment booking is supported; appointment screen has Existing Patient / New Patient choices.
8. Vitals are available during new-patient and follow-up visit creation, not hidden inside additional patient demographics.
9. Vitals can be recorded by Doctor or Receptionist according to Admin configuration. Saved vitals are automatically shown in the doctor's consultation.

## Backend correction
- Added CHECKED_IN appointment status to distinguish an arrived single-doctor patient from an unarrived BOOKED appointment.
- Single-doctor receptionist check-in sets CHECKED_IN; doctor can start consultation from it.

## Validation note
Python and browser JavaScript syntax were checked. Full pytest execution remains blocked in this environment because the project dependency `python-jose` is not installed.
