# Clinic ERP - SaaS Transition & Phase 1 Enhancement Plan

This plan outlines the changes required to transition the local, standalone Clinic ERP into a robust, multi-tenant SaaS application, while introducing the requested features and performing the requested technical audit.

## User Review Required
> [!IMPORTANT]
> - **SaaS Deployment Strategy:** Since you plan to support both Standalone Desktop and SaaS models, we will need an application flag (e.g. `IS_SAAS = True`) and to conditionally enforce cross-tenant restrictions if we use a shared database model. For local standalone installs, a default `tenant_id` is sufficient.
> - **New Role Addition:** The `Doctor_All` role will be introduced to override the rule that doctors can only view their own queue.

## Open Questions
> [!WARNING]
> - Will the SaaS version use PostgreSQL or another RDBMS instead of SQLite? (SQLite is not suited for multi-tenant concurrent writes on a large scale).
> - Should we add a **Pharmacy / Inventory module** now or defer it to Phase 2?
> - For notifications (SMS/Email), which gateway providers are you planning to use?

## Proposed Changes

### 1. Database & SaaS Optimization
The existing database schema in `src/adapters/db/orm_models.py` **already includes** `tenant_id` and `branch_id` for all primary tables, which is excellent. However, we need to optimize it for SaaS scale.

#### [MODIFY] src/adapters/db/orm_models.py
- **Changes:** Add **Composite Indexes** for `(tenant_id, branch_id)` on high-traffic tables (`appointments`, `patients`, `invoices`). Currently, they only have single-column indexes. Composite indexing drastically improves query speeds in multi-tenant shared databases.

### 2. Role-Based Access Control (RBAC) Updates
The current application supports `ADMIN`, `RECEPTIONIST`, and `DOCTOR`.

#### [MODIFY] src/domain/models/user.py
- **Changes:** Add `DOCTOR_ALL` to the `UserRole` enum.

#### [MODIFY] src/services/auth_service.py & src/services/appointment_service.py
- **Changes:** Implement authorization logic for `DOCTOR_ALL`.
  - While a regular `DOCTOR` can only see appointments where `doctor_id == current_user.id`, `DOCTOR_ALL` can view the entire clinic queue, similar to an Admin, but with clinical write access.

### 3. Gap Analysis (Missing Features)
Based on our review, the following essential SaaS/ERP features are currently missing and should be implemented:

1. **Audit Logs & Activity Tracking:** You have an `AuditLogORM` defined but need middleware to automatically log clinical data access (e.g. who viewed a patient history, who altered a prescription). This is crucial for HIPAA/compliance.
2. **Patient Portal API:** Current APIs are staff-focused. A set of read-only endpoints (protected by OTP) for patients to download their prescriptions and invoices is necessary.
3. **Automated Reminders:** A cron job/background service to poll upcoming appointments and dispatch SMS/WhatsApp notifications.
4. **Master Data Services (ICD-10, Drugs):** Doctors currently type symptoms and diagnoses as free text. We should add a master dictionary API to standardize data.
5. **Multi-Branch Context Switching:** The UI/API needs a way for `Doctor_All` and `Admin` users to switch their active `branch_id` session context without logging out.

### 4. Technical Audit & Codebase Optimization
- The current use of FastAPI with Domain Driven Design (DDD) is **very professional and scalable**.
- **Optimization:** We should separate the database initialization (`init_db`) from the web server startup for the SaaS model, using a migration tool like `Alembic`.
- **Optimization:** Change the JWT token structure to explicitly include `tenant_id` and `branch_id` as standard claims, ensuring that all API requests are automatically scoped by a global middleware, rather than relying solely on service-level checks.

### 5. Documentation
#### [MODIFY] README.md
- Will be completely overhauled to detail the Standalone vs. SaaS installation, new RBAC roles, and updated technical requirements (e.g. Postgres for SaaS, SQLite for local).
#### [NEW] USER_GUIDE.md
- A detailed manual for clinic staff on how to use Registration, Appointment Booking, Consultancy, and Billing modules.

## Verification Plan

### Automated Tests
- Run existing test suites (`pytest`).
- Write new unit tests ensuring `DOCTOR_ALL` can access other doctors' patients while `DOCTOR` gets a 403 Forbidden.

### Manual Verification
- Start the application locally.
- Log in as a newly created `Doctor_All` user and verify visibility of cross-doctor queues.
- Verify that `tenant_id` restrictions correctly isolate data when simulated.
