# Professional OPD v11 & v11.1 Release Notes

## Version 11.1 (Current)
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

## Version 11.0 (Baseline)
- Reception/Admin New Patient creates a visit in Scheduled/Booked state; it does NOT start consultation immediately.
- Reception must click Check-in when the patient arrives in the OPD lobby.
- Check-in transitions centralized visit status to Waiting / Checked In and places the patient in the assigned doctor's active queue with a daily token.
- Doctor New Patient may still open consultation directly for a single-doctor workflow.
- Multi-doctor workflow requires Consulting Doctor assignment and queue/token behavior.
- Today's OPD remains the shared central source of truth across Reception, Doctor, and Admin.
- Updated typography to a clean Aptos/Segoe UI system font stack.
