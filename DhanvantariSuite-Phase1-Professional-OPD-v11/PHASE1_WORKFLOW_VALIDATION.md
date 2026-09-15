# Phase 1 Workflow & Authorization Validation Matrix

This document is the acceptance checklist for the UI/backend. Every flow below must work without exposing irrelevant controls.

## A. Single-doctor clinic
1. Doctor login → Today.
2. New Patient → minimum fields → Register & Start Consultation.
3. Patient ID is automatic; **no token**.
4. Consultation opens directly with patient identity and visit type prefilled.
5. Doctor enters symptoms/diagnosis/prescription; completes consultation.
6. Billing opens/available; doctor may collect payment if enabled.
7. Receptionist login (if clinic has reception) can register/check-in but does not edit clinical consultation.
8. Doctor sees receptionist-created visit on Today without token.
9. Existing patient → search → history → Start Follow-up → direct consultation; no new patient record.

## B. Multi-doctor hospital/clinic
1. Admin creates Doctor A and Doctor B.
2. Reception registers new patient and selects doctor.
3. Save/Book creates patient + visit and generates a unique daily token.
4. Reception Check-in changes visit to IN_QUEUE.
5. Only assigned doctor sees the patient in their queue.
6. Doctor screen refreshes automatically; when idle, checked-in patient is opened automatically.
7. Doctor sees patient details + visit type + latest vitals + previous history.
8. Reception can record vitals when configured; doctor sees them without re-entry.
9. Doctor completes consultation; old history remains unchanged.
10. Billing can be collected by Reception or Doctor according to permission.
11. Admin can view billing and clinic data.

## C. Follow-up
- Mobile/name/patient ID search must find the existing patient.
- Duplicate mobile registration returns a helpful message directing the user to the existing patient.
- History is read-only while starting a new visit.
- New follow-up gets a new appointment/visit record.
- Multi-doctor follow-up gets a new token; single-doctor follow-up has no token.

## D. Vitals
- Admin can set Doctor, Receptionist or Both.
- Unauthorized role receives HTTP 403.
- BMI auto-calculates.
- Consultation consumes saved appointment vitals automatically.

## E. Billing
- No Billing login.
- Doctor/Receptionist payment permission controls collection.
- Admin has access.
- Invoice cannot be created twice for the same visit.
- Partial payment leaves an amount due.
- Payment receipt records who collected it.

## F. Authorization matrix
| Action | Admin | Doctor | Receptionist |
|---|---|---|---|
| Login | Yes | Yes | Yes |
| Register patient | Yes | Yes | Yes |
| Start new visit | Yes | Yes | Yes |
| Select doctor | Yes | No (self) | Yes when multi-doctor |
| Check-in | Yes | No | Yes |
| View clinical history | Yes | Yes | Configurable/view permission |
| Edit consultation | No in Phase 1 | Yes, own visit | No |
| Record vitals | Yes | Configurable | Configurable |
| Create/collect billing | Yes | Permission | Permission |
| Add users/settings | Yes | No | No |

## G. UX acceptance rules
- One primary action per screen.
- Never ask a doctor to select themselves.
- Never ask a user to re-enter patient data already stored.
- Never force a single-doctor clinic to use tokens.
- Never force a nurse/billing role that the clinic does not have.
- Search existing patient before allowing a new registration.
- Use clear labels: **New Patient**, **Existing Patient / Follow-up**, **Walk-in**, **Check-in**, **Open Consultation**, **Collect Payment**.
- If a control is not permitted for the current role, hide it rather than showing a confusing disabled workflow.
