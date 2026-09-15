# Dhanvantari Clinic ERP - SaaS & Desktop Edition

## Product Goal
A simple OPD, consultation, and billing application that works seamlessly as both a Multi-Tenant SaaS platform and a Single-Tenant Desktop application. Both models share the exact same codebase, architecture, and PostgreSQL database foundation.

## Roles
- **Admin**: Clinic/user/settings/report visibility; can view billing and all clinic records. Does not edit clinical notes.
- **Doctor_All**: Super-user access with permission to view the entire clinic queue across all doctors and manage all modules, including clinical edits for any patient.
- **Doctor**: Clinical workflow, patient registration, consultation, prescription, optional vitals, and payment collection. Restricted to their own queue.
- **Receptionist**: Patient registration, appointments, check-in/queue, optional vitals, billing/payment collection.

## Deployment Architecture
- **Unified Engine**: There are no separate applications for Desktop vs. SaaS. The Desktop version acts as a single-tenant instance (defaulting to local-clinic).
- **Database**: **PostgreSQL is required** for both SaaS and Desktop multi-tenant usage. The schema utilizes composite indexes on (tenant_id, branch_id) for high performance logical data isolation.

## Core Workflow Rules
### Single vs Multi Doctor Routing
- **Single active doctor**: No OPD token is generated. Registration goes straight to consultation.
- **Two or more active doctors**: Doctor assignment is required. A daily branch token is generated.
- **Doctor_All Visibility**: Users with the DOCTOR_ALL role bypass queue restrictions and can open any patient assigned to any doctor.

### Vitals & Billing
- Vitals recording can be configured by the Admin (Doctor, Receptionist, or Both).
- Billing can be collected by the doctor or receptionist according to their assigned permissions. Payment modes include Pending, Partial, and Paid.

## Security & SaaS Isolation
- All APIs are protected by JWT. 
- API dependencies (get_tenant_context) automatically scope database queries to the user's tenant_id and branch_id.
- For desktop standalone usage, a fallback tenant ID of local-clinic is injected automatically.

## Running the Application
### Prerequisites
- PostgreSQL running locally or in the cloud.
- Python 3.10+

### Setup
```powershell
# Set up database URL (update with your credentials)
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/clinic_erp"

# Install dependencies
python -m pip install -r requirements.txt

# Start the server
python -m uvicorn src.main:app --reload --port 8000
```
Open http://127.0.0.1:8000/ui/

### Demo Users (automatically seeded on empty DB):
- Admin: admin_user / adminpass123
- Receptionist: receptionist_user / receppass123
- Doctor: doctor_user / docpass123
