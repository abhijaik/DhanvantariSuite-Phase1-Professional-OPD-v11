import pytest
pytestmark = pytest.mark.skip(reason="Replaced by tests/test_phase1_workflows.py for Phase 1 Admin/Doctor/Receptionist workflow")
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.main import app
from src.adapters.api.dependencies import get_db
from src.adapters.db.orm_models import Base

# Setup in-memory SQLite database with StaticPool to share connection across sessions
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Apply the dependency override
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(name="client", scope="module")
def fixture_client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

def test_full_patient_consultation_billing_flow(client):
    headers = {
        "X-Tenant-ID": "test-tenant-1",
        "X-Branch-ID": "test-branch-main"
    }

    # 1. Register a user (Receptionist)
    reg_user_resp = client.post(
        "/api/auth/register",
        json={
            "username": "receptionist_jane",
            "password": "securepassword123",
            "full_name": "Jane Doe",
            "role": "RECEPTIONIST"
        },
        headers=headers
    )
    assert reg_user_resp.status_code == 200, reg_user_resp.text
    
    # 2. Login to get token
    login_resp = client.post(
        "/api/auth/login",
        data={
            "username": "receptionist_jane",
            "password": "securepassword123"
        },
        headers=headers
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    auth_header = {"Authorization": f"Bearer {token_data['access_token']}"}
    auth_headers = {**headers, **auth_header}

    # 3. Register a Patient
    patient_resp = client.post(
        "/api/patients/register",
        json={
            "full_name": "Aarav Sharma",
            "mobile": "9876543210", # Raw mobile number
            "date_of_birth": "1992-08-20",
            "age": 34,
            "gender": "Male",
            "address": "Mumbai, Maharashtra",
            "referred_by": "Google"
        },
        headers=auth_headers
    )
    assert patient_resp.status_code == 200, patient_resp.text
    patient = patient_resp.json()
    assert patient["patient_number"] is not None
    assert patient["mobile_normalized"] == "+919876543210" # Indian default prefix applied
    assert patient["referred_by"] == "Google"

    # 4. Prevent Patient Duplicate Mobile Profile
    dup_patient_resp = client.post(
        "/api/patients/register",
        json={
            "full_name": "Aarav Sharma Duplicate",
            "mobile": "+91 98765 43210", # Matches normalized representation
            "date_of_birth": "1992-08-20",
            "age": 34,
            "gender": "Male",
            "address": "Mumbai, Maharashtra"
        },
        headers=auth_headers
    )
    assert dup_patient_resp.status_code == 400
    assert "already registered" in dup_patient_resp.json()["detail"]

    # 5. Register a Doctor
    reg_doc_resp = client.post(
        "/api/auth/register",
        json={
            "username": "doctor_singh",
            "password": "docpassword123",
            "full_name": "Dr. Vivek Singh",
            "role": "DOCTOR"
        },
        headers=headers
    )
    assert reg_doc_resp.status_code == 200
    doctor = reg_doc_resp.json()

    # 6. Book an Appointment
    appt_resp = client.post(
        "/api/queue/book",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "appointment_date": "2026-07-20",
            "scheduled_time": "10:30:00",
            "visit_type": "New",
            "consultation_type": "OPD",
            "notes": "First check-up"
        },
        headers=auth_headers
    )
    assert appt_resp.status_code == 200, appt_resp.text
    appt = appt_resp.json()
    assert appt["queue_token"] == "T-01" # First token of the day

    # 7. Check-in the Patient (receptionist queue check-in)
    checkin_resp = client.post(
        f"/api/queue/{appt['id']}/checkin",
        headers=auth_headers
    )
    assert checkin_resp.status_code == 200
    assert checkin_resp.json()["status"] == "IN_QUEUE"

    # Log in as doctor
    doc_login_resp = client.post(
        "/api/auth/login",
        data={
            "username": "doctor_singh",
            "password": "docpassword123"
        },
        headers=headers
    )
    doc_token = doc_login_resp.json()["access_token"]
    doc_auth_headers = {**headers, "Authorization": f"Bearer {doc_token}"}

    # 8. Start Consultation
    start_consult_resp = client.post(
        f"/api/queue/{appt['id']}/start-consult",
        headers=doc_auth_headers
    )
    assert start_consult_resp.status_code == 200
    assert start_consult_resp.json()["status"] == "CONSULTING"

    # 9. Complete Consultation with Structured Prescription
    complete_resp = client.post(
        "/api/consultations/complete",
        json={
            "appointment_id": appt["id"],
            "symptoms": ["Dry Cough", "Mild Fever"],
            "diagnosis": "Seasonal Influenza",
            "prescription": [
                {
                    "medicine_name": "Paracetamol 500mg",
                    "dosage": "1-0-1",
                    "frequency": "After meals",
                    "duration": "3 days",
                    "food_relation": "After Food",
                    "instructions": "Drink plenty of warm water"
                },
                {
                    "medicine_name": "Cough Syrup 10ml",
                    "dosage": "0-0-1",
                    "frequency": "Before sleeping",
                    "duration": "5 days",
                    "food_relation": "Before Food"
                }
            ],
            "blood_pressure": "120/80",
            "weight": 70.5,
            "height": 175.2,
            "temperature": 98.6,
            "pulse_rate": 72,
            "follow_up_date": "2026-07-25",
            "notes": "Rest for 2 days. Avoid cold beverages."
        },
        headers=doc_auth_headers
    )
    assert complete_resp.status_code == 200, complete_resp.text
    consultation = complete_resp.json()
    assert len(consultation["prescription"]) == 2

    # Log in as Billing Staff (acting as receptionist with billing permission)
    reg_billing_resp = client.post(
        "/api/auth/register",
        json={
            "username": "billing_bob",
            "password": "billpassword123",
            "full_name": "Bob Smith",
            "role": "RECEPTIONIST",
            "can_collect_payment": True
        },
        headers=headers
    )
    assert reg_billing_resp.status_code == 200
    billing_login = client.post(
        "/api/auth/login",
        data={
            "username": "billing_bob",
            "password": "billpassword123"
        },
        headers=headers
    )
    bill_token = billing_login.json()["access_token"]
    bill_auth_headers = {**headers, "Authorization": f"Bearer {bill_token}"}

    # 10. Generate Invoice (Billing Engine)
    invoice_resp = client.post(
        "/api/billing/invoice",
        json={
            "appointment_id": appt["id"],
            "items": [
                {
                    "description": "General Consultation Charge",
                    "quantity": 1,
                    "unit_price": 500.00,
                    "tax_rate": 18.00, # 18% GST
                    "total": 0.00 # Recalculated by service
                },
                {
                    "description": "Influenza Diagnostic Kit",
                    "quantity": 1,
                    "unit_price": 200.00,
                    "tax_rate": 5.00, # 5% GST
                    "total": 0.00
                }
            ],
            "discount_amount": 50.00,
            "payment_mode": "UPI",
            "payment_status": "PENDING"
        },
        headers=bill_auth_headers
    )
    assert invoice_resp.status_code == 200, invoice_resp.text
    invoice = invoice_resp.json()
    
    # Check Calculations:
    # Item 1 total: 500 + 18% = 590
    # Item 2 total: 200 + 5% = 210
    # Subtotal (before tax): 500 + 200 = 700
    # Tax: 90 + 10 = 100
    # Discount: 50
    # Grand Total: 700 + 100 - 50 = 750
    assert float(invoice["subtotal"]) == 700.00
    assert float(invoice["tax_amount"]) == 100.00
    assert float(invoice["discount_amount"]) == 50.00
    assert float(invoice["total_amount"]) == 750.00

    # 11. Complete Invoice Payment
    pay_resp = client.post(
        f"/api/billing/invoice/{invoice['id']}/pay",
        json={"payment_mode": "UPI"},
        headers=bill_auth_headers
    )
    assert pay_resp.status_code == 200
    assert pay_resp.json()["payment_status"] == "PAID"

    # 12. Retrieve PDF Invoice Receipt (Multi-lingual test)
    print_resp = client.get(
        f"/api/billing/invoice/{invoice['id']}/print?lang=mr", # Marathi language print request
        headers=bill_auth_headers
    )
    assert print_resp.status_code == 200
    assert print_resp.headers["content-type"] == "application/pdf"
    assert len(print_resp.content) > 1000 # Verify PDF contains binary bytes data

def test_superdoc_role_bypass(client):
    headers = {
        "X-Tenant-ID": "test-tenant-1",
        "X-Branch-ID": "test-branch-main"
    }

    # 1. Register a SUPERDOC user
    reg_sd_resp = client.post(
        "/api/auth/register",
        json={
            "username": "superdoc_jane",
            "password": "superpassword123",
            "full_name": "Dr. Jane Super",
            "role": "SUPERDOC"
        },
        headers=headers
    )
    assert reg_sd_resp.status_code == 200, reg_sd_resp.text
    sd_user = reg_sd_resp.json()

    # 2. Login
    login_resp = client.post(
        "/api/auth/login",
        data={
            "username": "superdoc_jane",
            "password": "superpassword123"
        },
        headers=headers
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    sd_auth_headers = {**headers, "Authorization": f"Bearer {token_data['access_token']}"}

    # 3. SuperDoc registers a Patient (Normally Receptionist/Admin only)
    patient_resp = client.post(
        "/api/patients/register",
        json={
            "full_name": "Siddharth Roy",
            "mobile": "9998887770",
            "date_of_birth": "1988-12-05",
            "age": 37,
            "gender": "Male",
            "address": "Pune, India"
        },
        headers=sd_auth_headers
    )
    assert patient_resp.status_code == 200, patient_resp.text
    patient = patient_resp.json()

    # 4. SuperDoc books an appointment (Normally Receptionist/Admin only)
    appt_resp = client.post(
        "/api/queue/book",
        json={
            "patient_id": patient["id"],
            "doctor_id": sd_user["id"],
            "appointment_date": "2026-07-20",
            "scheduled_time": "14:00:00",
            "visit_type": "New",
            "consultation_type": "OPD",
            "notes": "SuperDoc test consult"
        },
        headers=sd_auth_headers
    )
    assert appt_resp.status_code == 200, appt_resp.text
    appt = appt_resp.json()

    # 5. SuperDoc starts and completes consultation (Normally Doctor/Admin only)
    start_resp = client.post(
        f"/api/queue/{appt['id']}/start-consult",
        headers=sd_auth_headers
    )
    assert start_resp.status_code == 200

    complete_resp = client.post(
        "/api/consultations/complete",
        json={
            "appointment_id": appt["id"],
            "symptoms": ["Headache"],
            "diagnosis": "Stress",
            "prescription": [
                {
                    "medicine_name": "Aspirin",
                    "dosage": "1-0-0",
                    "frequency": "After lunch",
                    "duration": "1 day",
                    "food_relation": "After Food"
                }
            ],
            "blood_pressure": "118/75",
            "weight": 68.0,
            "height": 172.0,
            "temperature": 98.4,
            "pulse_rate": 68,
            "follow_up_date": "2026-07-27"
        },
        headers=sd_auth_headers
    )
    assert complete_resp.status_code == 200, complete_resp.text

def test_vitals_workflow_and_partial_payments_api(client):
    headers = {
        "X-Tenant-ID": "test-tenant-1",
        "X-Branch-ID": "test-branch-main"
    }

    # 1. Register and Login Admin
    client.post("/api/auth/register", json={"username": "adm", "password": "pass", "full_name": "Admin", "role": "ADMIN"}, headers=headers)
    adm_login = client.post("/api/auth/login", data={"username": "adm", "password": "pass"}, headers=headers).json()
    adm_auth = {**headers, "Authorization": f"Bearer {adm_login['access_token']}"}

    # 2. Register and Login Nurse (acting as receptionist with vitals permission)
    client.post("/api/auth/register", json={"username": "nurse_angela", "password": "pass", "full_name": "Nurse Angela", "role": "RECEPTIONIST", "can_enter_vitals": True}, headers=headers)
    nurse_login = client.post("/api/auth/login", data={"username": "nurse_angela", "password": "pass"}, headers=headers).json()
    nurse_auth = {**headers, "Authorization": f"Bearer {nurse_login['access_token']}"}

    # 3. Admin configures vitals recording role to Receptionist
    config_resp = client.post("/api/vitals/config", json={"recorder_role": "Receptionist"}, headers=adm_auth)
    assert config_resp.status_code == 200
    assert config_resp.json()["recorder_role"] == "Receptionist"

    # 4. Book Appointment
    pat_resp = client.post("/api/patients/register", json={"full_name": "Pat", "mobile": "9990001111", "date_of_birth": "2000-01-01", "age": 26, "gender": "Female", "address": "M"}, headers=adm_auth)
    pat = pat_resp.json()
    
    doc_resp = client.post("/api/auth/register", json={"username": "doc_v", "password": "pass", "full_name": "Dr V", "role": "DOCTOR"}, headers=headers).json()

    appt_resp = client.post("/api/queue/book", json={
        "patient_id": pat["id"],
        "doctor_id": doc_resp["id"],
        "appointment_date": "2026-07-20",
        "scheduled_time": "12:00:00",
        "visit_type": "New Patient",
        "consultation_type": "Gynecology Consultation",
        "consultation_subtype": "Irregular Periods"
    }, headers=adm_auth)
    appt = appt_resp.json()

    # 5. Nurse records vitals (Checks BMI calculation: 70kg / 1.75m^2 = 22.86)
    vitals_resp = client.post("/api/vitals/record", json={
        "appointment_id": appt["id"],
        "blood_pressure": "120/80",
        "weight": 70.0,
        "height": 175.0,
        "temperature": 98.6,
        "pulse": 72,
        "spo2": 99,
        "respiratory_rate": 18
    }, headers=nurse_auth)
    assert vitals_resp.status_code == 200
    assert vitals_resp.json()["bmi"] == 22.86

    # 6. Check that a user without vitals permission is forbidden from recording vitals
    client.post("/api/auth/register", json={"username": "bad_rec", "password": "pass", "full_name": "Bad Rec", "role": "RECEPTIONIST", "can_enter_vitals": False}, headers=headers)
    bad_login = client.post("/api/auth/login", data={"username": "bad_rec", "password": "pass"}, headers=headers).json()
    bad_auth = {**headers, "Authorization": f"Bearer {bad_login['access_token']}"}
    bad_vitals = client.post("/api/vitals/record", json={"appointment_id": appt["id"], "weight": 72.0}, headers=bad_auth)
    assert bad_vitals.status_code == 403

    # 7. Doctor completes consultation (Vitals pre-fill verify)
    doc_auth = {**headers, "Authorization": f"Bearer {client.post('/api/auth/login', data={'username': 'doc_v', 'password': 'pass'}, headers=headers).json()['access_token']}"}
    client.post(f"/api/queue/{appt['id']}/start-consult", headers=doc_auth)
    
    comp_resp = client.post("/api/consultations/complete", json={
        "appointment_id": appt["id"],
        "symptoms": ["Pain"],
        "diagnosis": "None",
        "prescription": []
    }, headers=doc_auth)
    assert comp_resp.status_code == 200
    consultation = comp_resp.json()
    assert consultation["blood_pressure"] == "120/80"
    assert consultation["bmi"] == 22.86
    assert consultation["spo2"] == 99

    # 8. Receptionist generates invoice
    inv_resp = client.post("/api/billing/invoice", json={
        "appointment_id": appt["id"],
        "items": [],
        "consultation_charges": 500.0,
        "discount_amount": 0.0,
        "payment_mode": "CASH",
        "payment_status": "PENDING"
    }, headers=adm_auth)
    assert inv_resp.status_code == 200
    inv = inv_resp.json()
    assert float(inv["total_amount"]) == 500.0
    assert float(inv["amount_due"]) == 500.0

    # 9. Partial Pay 200
    pay1_resp = client.post(f"/api/billing/invoice/{inv['id']}/pay", json={"payment_mode": "CASH", "amount": 200.0}, headers=adm_auth)
    assert pay1_resp.status_code == 200
    assert pay1_resp.json()["payment_status"] == "PARTIAL"
    assert float(pay1_resp.json()["amount_paid"]) == 200.0
    assert float(pay1_resp.json()["amount_due"]) == 300.0

    # 10. Pay the rest
    pay2_resp = client.post(f"/api/billing/invoice/{inv['id']}/pay", json={"payment_mode": "CASH", "amount": 300.0}, headers=adm_auth)
    assert pay2_resp.status_code == 200
    assert pay2_resp.json()["payment_status"] == "PAID"
    assert float(pay2_resp.json()["amount_paid"]) == 500.0
    assert float(pay2_resp.json()["amount_due"]) == 0.0

def test_settings_endpoints(client):
    headers = {
        "X-Tenant-ID": "test-tenant-1",
        "X-Branch-ID": "test-branch-main"
    }
    
    # Register and Login Admin
    client.post("/api/auth/register", json={"username": "set_admin", "password": "pass", "full_name": "Set Admin", "role": "ADMIN"}, headers=headers)
    login_resp = client.post("/api/auth/login", data={"username": "set_admin", "password": "pass"}, headers=headers).json()
    auth_headers = {**headers, "Authorization": f"Bearer {login_resp['access_token']}"}
    
    # 1. Get default settings
    get_resp = client.get("/api/settings", headers=auth_headers)
    assert get_resp.status_code == 200
    settings = get_resp.json()
    assert settings["clinic_name"] == "My Local Clinic"
    
    # 2. Update settings
    update_data = {
        "clinic_name": "Premium Care Clinic",
        "clinic_address": "456 Parkway Road",
        "phone": "555-9876",
        "email": "premium@care.com",
        "currency": "USD",
        "tax_enabled": True,
        "invoice_prefix": "PREM",
        "invoice_language_default": "en",
        "appointment_duration": 20,
        "vitals_entry_by": "Doctor"
    }
    post_resp = client.post("/api/settings", json=update_data, headers=auth_headers)
    assert post_resp.status_code == 200
    assert post_resp.json()["clinic_name"] == "Premium Care Clinic"
    assert post_resp.json()["currency"] == "USD"
    
    # 3. Verify get retrieves updated values
    get_updated = client.get("/api/settings", headers=auth_headers)
    assert get_updated.status_code == 200
    assert get_updated.json()["clinic_name"] == "Premium Care Clinic"
    assert get_updated.json()["vitals_entry_by"] == "Doctor"

def test_register_patient_and_visit_endpoint(client):
    headers = {
        "X-Tenant-ID": "test-tenant-1",
        "X-Branch-ID": "test-branch-main"
    }
    
    # Register and Login Admin
    client.post("/api/auth/register", json={"username": "visit_admin", "password": "pass", "full_name": "Visit Admin", "role": "ADMIN"}, headers=headers)
    login_resp = client.post("/api/auth/login", data={"username": "visit_admin", "password": "pass"}, headers=headers).json()
    auth_headers = {**headers, "Authorization": f"Bearer {login_resp['access_token']}"}
    
    # Register Doctor to assign the visit
    doc = client.post("/api/auth/register", json={"username": "visit_doc", "password": "pass", "full_name": "Dr. Visit", "role": "DOCTOR"}, headers=headers).json()
    
    # Send registration + visit payload
    payload = {
        "full_name": "Fast Patient",
        "mobile": "9765432100",
        "date_of_birth": "1995-05-15",
        "age": 31,
        "gender": "Male",
        "address": "456 Main St",
        "alternate_number": "1234567890",
        "allergies": "Nuts",
        "medical_notes": "None",
        
        "doctor_id": doc["id"],
        "visit_type": "Follow-Up",
        "consultation_type": "General Consultation",
        "consultation_subtype": "Routine Health Check",
        "notes": "Fast booking test"
    }
    
    resp = client.post("/api/patients/register-visit", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "patient" in data
    assert "appointment" in data
    assert data["patient"]["full_name"] == "Fast Patient"
    assert data["patient"]["mobile_normalized"] == "+919765432100"
    assert data["appointment"]["visit_type"] == "Follow-Up"
    assert data["appointment"]["queue_token"] == "T-01"

def test_user_permissions_management(client):
    headers = {
        "X-Tenant-ID": "test-tenant-1",
        "X-Branch-ID": "test-branch-main"
    }
    
    # Register and Login Admin
    client.post("/api/auth/register", json={"username": "perm_admin", "password": "pass", "full_name": "Perm Admin", "role": "ADMIN"}, headers=headers)
    login_resp = client.post("/api/auth/login", data={"username": "perm_admin", "password": "pass"}, headers=headers).json()
    auth_headers = {**headers, "Authorization": f"Bearer {login_resp['access_token']}"}
    
    # Register a standard Receptionist
    rec = client.post("/api/auth/register", json={"username": "perm_rec", "password": "pass", "full_name": "Perm Rec", "role": "RECEPTIONIST"}, headers=headers).json()
    
    # 1. Fetch user list as admin
    users_resp = client.get("/api/auth/users", headers=auth_headers)
    assert users_resp.status_code == 200
    users = users_resp.json()
    assert len(users) > 0
    rec_user = next(u for u in users if u["username"] == "perm_rec")
    assert rec_user["can_collect_payment"] is True
    
    # 2. Update receptionist permissions to disable payment collection and deactivate status
    update_data = {
        "can_collect_payment": False,
        "can_enter_vitals": True,
        "can_view_clinical_history": False,
        "can_edit_clinical_data": False,
        "status": "Inactive"
    }
    update_resp = client.post(f"/api/auth/users/{rec['id']}/permissions", json=update_data, headers=auth_headers)
    assert update_resp.status_code == 200
    updated_rec = update_resp.json()
    assert updated_rec["can_collect_payment"] is False
    assert updated_rec["status"] == "Inactive"
    
    # 3. Verify deactivated receptionist cannot login
    fail_login = client.post("/api/auth/login", data={"username": "perm_rec", "password": "pass"}, headers=headers)
    assert fail_login.status_code == 401


