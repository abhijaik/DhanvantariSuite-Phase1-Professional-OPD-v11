# Phase 1 Workflow & Authorization Validation Matrix

This document is the acceptance checklist for the UI and backend. Every flow below must work reliably without exposing irrelevant controls.

## A. Authentication & Access
1. **Password Login**: User enters username and password to authenticate.
2. **OTP Login**: User enters registered username or 10-digit mobile number, receives 6-digit OTP (5-minute TTL, max 3 attempts), enters OTP to sign in seamlessly.
3. **Multilingual Switcher**: Can change UI locale to English, Marathi, Hindi, or Arabic (with RTL layout support) on both login and dashboard.

## B. Single-doctor clinic
1. Doctor login → Today.
2. New Patient → minimum fields → Register & Start Consultation.
3. Patient ID is automatic; **no token**.
4. Consultation opens directly with patient identity and visit type prefilled.
5. Doctor enters symptoms/diagnosis/prescription; completes consultation.
6. Billing opens/available; doctor may collect payment if enabled.
7. Receptionist login (if clinic has reception) can register/check-in but does not edit clinical consultation.
8. Doctor sees receptionist-created visit on Today without token.
9. Existing patient → search → history → Start Follow-up → direct consultation; no new patient record.

## C. Multi-doctor hospital/clinic
1. Admin creates Doctor A and Doctor B.
2. Reception registers new patient and selects doctor.
3. Save/Book creates patient + visit and generates a unique daily token.
4. Reception or Doctor Check-in changes visit to IN_QUEUE / CHECKED_IN.
5. Only assigned doctor sees the patient in their queue (Doctor_All can view all).
6. Doctor and Reception screens synchronize automatically every 3 seconds; live 5-card KPI counters reflect today's exact state.
7. Doctor completes consultation; patient transitions to Completed state and remains visible in Today's list with a green Completed badge.
8. Billing can be collected by Reception or Doctor according to permission via 1-click "Collect Payment" or Billing tab.
9. Admin can view billing and clinic data.

## D. Multilingual Prescriptions
1. Doctor or receptionist clicks **Print Prescription** from consultation or completed queue.
2. Language modal offers: English, Marathi, Hindi, or Arabic.
3. PDF renders with native Unicode typography (Devanagari for MR/HI, Reshaped RTL for Arabic).
4. **Drug Safety Guard**: Medicine brand names remain strictly in English/Latin script while instructions, vitals, food relations, and clinical headers are translated.

## E. Follow-up
- Mobile/name/patient ID search finds the existing patient.
- Duplicate mobile registration alerts user and directs to existing patient.
- History is read-only while starting a new visit.
- New follow-up gets a new appointment/visit record; prior history is never overwritten.
- Multi-doctor follow-up gets a new token; single-doctor follow-up has no token.

## F. Vitals
- Admin can configure vitals recorder: Doctor, Receptionist, or Both.
- Unauthorized role receives HTTP 403 if attempting unauthorized entry.
- BMI auto-calculates from height and weight.
- Consultation consumes saved appointment vitals automatically.

## G. Billing
- Doctor/Receptionist payment permission controls collection.
- Admin has full oversight.
- Invoice cannot be created twice for the same visit.
- Partial payment leaves an amount due.
- Payment receipt records authenticated collector context.

## H. Authorization matrix
| Action | Admin | Doctor | Doctor_All | Receptionist |
|---|:---:|:---:|:---:|:---:|
| Login (Password or OTP) | Yes | Yes | Yes | Yes |
| Change UI Language (EN, MR, HI, AR) | Yes | Yes | Yes | Yes |
| Register patient | Yes | Yes | Yes | Yes |
| Start new visit | Yes | Yes | Yes | Yes |
| Select doctor | Yes | No (self) | Yes | Yes (when multi-doctor) |
| Check-in patient | Yes | Yes (assigned) | Yes (all) | Yes |
| View clinical history | Yes | Yes | Yes | Configurable/view permission |
| Edit consultation | No (read-only) | Yes (own visit) | Yes (any patient) | No |
| Print Multilingual Prescription | Yes | Yes | Yes | Yes |
| Record vitals | Yes | Configurable | Configurable | Configurable |
| Create/collect billing | Yes | Permission | Permission | Permission |
| Add users/settings | Yes | No | No | No |

## I. UX acceptance rules
- One primary action per screen.
- Real-time synchronization across dashboards (3-second cadence).
- Completed patients never disappear from today's visit list.
- Medicine names are never transliterated/corrupted in prescriptions.
- Never ask a doctor to select themselves.
- Never ask a user to re-enter patient data already stored.
- Never force a single-doctor clinic to use tokens.
- Clear, actionable labels: **New Patient**, **Find Patient**, **Check-in**, **Open Consultation**, **Collect Payment**, **Print Prescription**.
