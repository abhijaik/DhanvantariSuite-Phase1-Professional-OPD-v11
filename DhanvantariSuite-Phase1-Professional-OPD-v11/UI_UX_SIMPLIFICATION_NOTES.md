# Phase 1 UI/UX Simplification

## User-facing quick actions
The Today/OPD screen intentionally exposes only three primary actions:

- **+ New Patient** — registers the patient and starts today's appropriate visit automatically.
- **Find Patient** — searches an existing patient and starts the appropriate new visit/follow-up flow.
- **Appointments** — used for scheduled/future visits.

Billing remains in the main navigation instead of being duplicated as a top quick-action button.

## Workflow principle
Users should not need to understand internal concepts such as registration, check-in, token, appointment, and visit. The system chooses the correct workflow from clinic configuration, active doctor count, role and visit context.

### Single doctor
New Patient -> Save & Start Consultation -> direct consultation. No token.

Existing patient -> Find Patient -> Start Visit -> previous history available -> direct follow-up consultation. No token.

### Multi-doctor hospital/clinic
New Patient -> select doctor -> Save & Start Visit -> token/check-in -> assigned doctor's queue.

Existing patient -> Find Patient -> Start Visit -> select doctor if required -> token/check-in -> assigned doctor's queue.

## UI wording rules
Avoid exposing these as primary actions:
- Register & Check-in
- Register Patient Only
- Find Patient / Follow-up
- New Patient & Start Visit

Those are implementation/workflow concepts, not user tasks.
