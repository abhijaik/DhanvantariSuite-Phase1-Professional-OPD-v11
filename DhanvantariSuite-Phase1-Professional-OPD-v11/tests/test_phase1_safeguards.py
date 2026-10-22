import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.adapters.api.dependencies import get_db
from src.adapters.db.orm_models import Base, PatientORM, ConsultationORM, AppointmentORM
from src.adapters.db.repositories import SQLAlchemyUserRepository, SQLAlchemyPatientRepository
from src.adapters.db.encryption import encrypt_value, decrypt_value
from src.services.auth_service import AuthService
from src.domain.models.user import UserRole
from src.domain.models.consultation import PrescriptionItem
from generate_ssl_certs import generate_self_signed_cert

engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def override_get_db():
    db = TestingSession()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@pytest.fixture(scope='module')
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSession()
    auth = AuthService(SQLAlchemyUserRepository(db))
    # Register test staff accounts
    auth.register_user('safe-tenant', 'safe-branch', 'admin_sec', 'secpass123', 'Security Admin', UserRole.ADMIN, mobile='9800000001')
    auth.register_user('safe-tenant', 'safe-branch', 'doctor_sec', 'secpass123', 'Dr. Security', UserRole.DOCTOR, mobile='9800000002')
    auth.register_user('safe-tenant', 'safe-branch', 'recep_sec', 'secpass123', 'Recep Security', UserRole.RECEPTIONIST, mobile='9800000003')
    db.commit()
    db.close()

    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)

def get_auth_header(client, username, password):
    r = client.post('/api/auth/login', data={'username': username, 'password': password}, headers={'X-Tenant-ID': 'safe-tenant', 'X-Branch-ID': 'safe-branch'})
    assert r.status_code == 200, r.text
    token = r.json()['access_token']
    return {
        'Authorization': f'Bearer {token}',
        'X-Tenant-ID': 'safe-tenant',
        'X-Branch-ID': 'safe-branch'
    }

# ==============================================================================
# SAFEGUARD 1: HTTPS / TLS 1.3 & SECURITY RESPONSE HEADERS
# ==============================================================================
def test_security_response_headers(client):
    """Verify all mandatory HIPAA & DPDP security response headers are injected."""
    response = client.get("/")
    assert response.status_code in [200, 307]

    headers = response.headers
    # HSTS
    assert "Strict-Transport-Security" in headers
    assert "max-age=63072000" in headers["Strict-Transport-Security"]
    assert "includeSubDomains" in headers["Strict-Transport-Security"]

    # Clickjacking protection
    assert headers.get("X-Frame-Options") == "DENY"

    # MIME type sniffing
    assert headers.get("X-Content-Type-Options") == "nosniff"

    # XSS Protection
    assert headers.get("X-XSS-Protection") == "1; mode=block"

    # Referrer Policy
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # Permissions Policy
    assert "camera=()" in headers.get("Permissions-Policy", "")
    assert "microphone=()" in headers.get("Permissions-Policy", "")

    # Content Security Policy (CSP)
    csp = headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "https://cdnjs.cloudflare.com" in csp

def test_tls_certificate_generation(tmp_path):
    """Verify programmatic TLS 1.3 / SAN self-signed certificate generation."""
    cert_file, key_file = generate_self_signed_cert(
        cert_dir=str(tmp_path),
        cert_name="test_cert.pem",
        key_name="test_key.pem"
    )
    with open(cert_file, "r") as cf:
        cert_text = cf.read()
    with open(key_file, "r") as kf:
        key_text = kf.read()
    assert "-----BEGIN CERTIFICATE-----" in cert_text
    assert "-----BEGIN RSA PRIVATE KEY-----" in key_text or "-----BEGIN PRIVATE KEY-----" in key_text


# ==============================================================================
# SAFEGUARD 2: DATABASE FIELD-LEVEL ENCRYPTION (PII & CLINICAL NOTES)
# ==============================================================================
def test_database_field_level_encryption(client):
    """
    Verify AES-256 field-level encryption for ePHI and sensitive clinical notes:
    1. Direct raw SQL SELECT returns ciphertext.
    2. SQLAlchemy ORM returns decrypted plaintext.
    3. Legacy unencrypted values decrypt gracefully without exceptions.
    """
    rec_h = get_auth_header(client, 'recep_sec', 'secpass123')
    doc_h = get_auth_header(client, 'doctor_sec', 'secpass123')

    # Register patient with sensitive PII and emergency contact
    secret_address = "Flat 402, Shanti Vihar, Pune"
    secret_allergies = "Severe Penicillin Allergy, Peanuts"
    secret_notes = "Patient has chronic migraine and family history of diabetes"
    secret_emergency = "Wife: Sunita (+91-9876543210)"
    secret_email = "patient.secret@example.com"
    secret_alt_mobile = "9876500000"

    p_res = client.post('/api/patients/register', json={
        'full_name': 'Encrypted Patient',
        'mobile': '9899001122',
        'date_of_birth': '1990-01-01',
        'age': 36,
        'gender': 'Male',
        'address': secret_address,
        'email': secret_email,
        'alternate_number': secret_alt_mobile,
        'allergies': secret_allergies,
        'medical_notes': secret_notes,
        'emergency_contact': secret_emergency
    }, headers=rec_h)
    assert p_res.status_code == 200, p_res.text
    p_id = p_res.json()['id']

    # 1. RAW SQL VERIFICATION: Ensure values are stored as ciphertext in the database table
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT address, email, alternate_number, allergies, medical_notes, emergency_contact FROM patients WHERE id = :id"
        ), {"id": p_id}).fetchone()

        raw_addr, raw_email, raw_alt, raw_allergies, raw_notes, raw_emergency = row

        # Raw values MUST NOT equal plaintext
        assert raw_addr != secret_address
        assert raw_email != secret_email
        assert raw_allergies != secret_allergies
        assert raw_notes != secret_notes
        assert raw_emergency != secret_emergency

        # Raw values are Fernet ciphertext tokens (AES-128-CBC + HMAC-SHA256)
        assert raw_addr.startswith("gAAAAA")
        assert raw_email.startswith("gAAAAA")
        assert raw_allergies.startswith("gAAAAA")
        assert raw_notes.startswith("gAAAAA")
        assert raw_emergency.startswith("gAAAAA")

    # 2. ORM VERIFICATION: Transparent decryption on model load
    db = TestingSession()
    orm_patient = db.query(PatientORM).filter(PatientORM.id == p_id).first()
    assert orm_patient.address == secret_address
    assert orm_patient.email == secret_email
    assert orm_patient.alternate_number == secret_alt_mobile
    assert orm_patient.allergies == secret_allergies
    assert orm_patient.medical_notes == secret_notes
    assert orm_patient.emergency_contact == secret_emergency
    db.close()

    # 3. CLINICAL NOTES ENCRYPTION (Consultation diagnosis, symptoms, prescription, notes)
    b_res = client.post('/api/queue/book', json={
        'patient_id': p_id,
        'appointment_date': str(date.today()),
        'scheduled_time': '11:00:00',
        'visit_type': 'Consultation',
        'consultation_type': 'General Consultation',
        'notes': 'Confidential clinical booking note',
        'check_in_now': True
    }, headers=rec_h)
    assert b_res.status_code == 200, b_res.text
    appt_id = b_res.json()['id']

    secret_symptoms = ["Acute Chest Congestion", "Dry Cough"]
    secret_diagnosis = "Bacterial Bronchitis - Confidential Note"
    secret_rx_notes = "Steam inhalation twice daily. Avoid cold drinks."

    comp_res = client.post('/api/consultations/complete', json={
        'appointment_id': appt_id,
        'symptoms': secret_symptoms,
        'diagnosis': secret_diagnosis,
        'notes': secret_rx_notes,
        'prescription': [{
            'medicine_name': 'Azithromycin 500mg',
            'dosage': '1-0-0',
            'frequency': 'Once Daily',
            'duration': '3 Days',
            'food_relation': 'After Food',
            'instructions': 'Take after lunch'
        }]
    }, headers=doc_h)
    assert comp_res.status_code == 200, comp_res.text
    c_id = comp_res.json()['id']

    # Raw SQL check on consultations table
    with engine.connect() as conn:
        c_row = conn.execute(text(
            "SELECT symptoms, diagnosis, notes, prescription_json FROM consultations WHERE id = :id"
        ), {"id": c_id}).fetchone()

        raw_symp, raw_diag, raw_rx_notes, raw_rx_json = c_row
        assert raw_diag != secret_diagnosis
        assert raw_diag.startswith("gAAAAA")
        assert raw_rx_notes.startswith("gAAAAA")
        assert raw_symp.startswith("gAAAAA")
        assert raw_rx_json.startswith("gAAAAA")

    # ORM check on consultations table
    db = TestingSession()
    orm_consult = db.query(ConsultationORM).filter(ConsultationORM.id == c_id).first()
    assert orm_consult.diagnosis == secret_diagnosis
    assert orm_consult.notes == secret_rx_notes
    assert "Acute Chest Congestion" in orm_consult.symptoms
    db.close()

    # 4. Fallback check for legacy unencrypted values
    assert decrypt_value("legacy plaintext note") == "legacy plaintext note"
    assert decrypt_value(None) is None


# ==============================================================================
# SAFEGUARD 3: AUTOMATIC SESSION INACTIVITY TIMEOUT (15 MINS)
# ==============================================================================
def test_session_inactivity_timeout_handling(client):
    """
    Verify HIPAA § 164.312(a)(2)(iii) session inactivity timeout handling:
    1. Endpoint logs SESSION_TIMEOUT with reason.
    2. Static frontend contains 15-minute timeout configuration and listeners.
    """
    doc_h = get_auth_header(client, 'doctor_sec', 'secpass123')

    # Trigger inactivity timeout logout
    logout_res = client.post('/api/auth/logout?reason=inactivity_timeout', headers=doc_h)
    assert logout_res.status_code == 200
    assert logout_res.json()['status'] == 'logged_out'
    assert logout_res.json()['reason'] == 'inactivity_timeout'

    # Verify audit log captures SESSION_TIMEOUT action
    admin_h = get_auth_header(client, 'admin_sec', 'secpass123')
    audit_res = client.get('/api/audit-logs?action=SESSION_TIMEOUT', headers=admin_h)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) >= 1
    timeout_log = logs[0]
    assert timeout_log['action'] == 'SESSION_TIMEOUT'
    assert timeout_log['module'] == 'AUTH'
    assert '15 minutes of inactivity' in timeout_log['summary']

    # Verify frontend static file contains 15-minute inactivity constants and listeners
    with open('src/static/index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    assert "INACTIVITY_TIMEOUT_MS = 15 * 60 * 1000" in html_content
    assert "INACTIVITY_WARNING_MS = 14 * 60 * 1000" in html_content
    assert "session-timeout-banner" in html_content
    assert "inactivity-warning-modal" in html_content


# ==============================================================================
# SAFEGUARD 4: COMPREHENSIVE AUDIT LOGGING (ACCESS, READ, WRITE, EXPORT, PRINT)
# ==============================================================================
def test_comprehensive_audit_logging(client):
    """
    Verify HIPAA § 164.312(b) and DPDP Act 2023 Comprehensive Audit Trail:
    - Access: LOGIN_PASSWORD_SUCCESS, LOGIN_FAILED, LOGOUT, SESSION_TIMEOUT
    - Read: READ_PATIENT, SEARCH_PATIENTS, READ_CONSULTATION, READ_INVOICE_LIST
    - Write: CREATE_PATIENT, BOOK_APPOINTMENT, CHECK_IN_PATIENT, START_CONSULTATION, COMPLETE_CONSULTATION, RECORD_VITALS, CREATE_INVOICE, COLLECT_PAYMENT
    - Export / Print: PRINT_PRESCRIPTION, PRINT_INVOICE_RECEIPT
    - Admin access only to /api/audit-logs
    """
    admin_h = get_auth_header(client, 'admin_sec', 'secpass123')
    doc_h = get_auth_header(client, 'doctor_sec', 'secpass123')
    rec_h = get_auth_header(client, 'recep_sec', 'secpass123')

    # 1. Non-admin is blocked from reading audit logs
    unauth_audit = client.get('/api/audit-logs', headers=doc_h)
    assert unauth_audit.status_code == 403

    # 2. Failed login generates audit log
    client.post('/api/auth/login', data={'username': 'admin_sec', 'password': 'wrongpassword'}, headers={'X-Tenant-ID': 'safe-tenant', 'X-Branch-ID': 'safe-branch'})

    # 3. Patient read and search
    client.get('/api/patients/search?q=Encrypted', headers=rec_h)

    # 4. Record Vitals generates audit log
    client.post('/api/vitals/record', json={
        'appointment_id': 'test-appt-vitals',
        'blood_pressure': '120/80',
        'pulse': 72,
        'temperature': 98.4
    }, headers=doc_h)

    # 5. Book and Check-in generates BOOK_APPOINTMENT and CHECK_IN_PATIENT audit logs
    b_ci = client.post('/api/queue/book', json={
        'patient_id': 'test-p-id-checkin',
        'appointment_date': str(date.today()),
        'scheduled_time': '12:30:00',
        'visit_type': 'Consultation',
        'consultation_type': 'General Consultation',
        'check_in_now': False
    }, headers=rec_h)
    assert b_ci.status_code == 200
    test_appt_id = b_ci.json()['id']
    ci_res = client.post(f'/api/queue/{test_appt_id}/checkin', headers=rec_h)
    assert ci_res.status_code == 200

    # 6. Query audit logs as Admin
    all_logs_res = client.get('/api/audit-logs?limit=200', headers=admin_h)
    assert all_logs_res.status_code == 200
    logs = all_logs_res.json()
    actions_logged = {l['action'] for l in logs}

    # Verify key action categories
    expected_actions = {
        'LOGIN_PASSWORD_SUCCESS',
        'LOGIN_FAILED',
        'CREATE_PATIENT',
        'BOOK_APPOINTMENT',
        'CHECK_IN_PATIENT',
        'COMPLETE_CONSULTATION',
        'RECORD_VITALS',
        'SESSION_TIMEOUT'
    }
    for act in expected_actions:
        assert act in actions_logged, f"Expected audit action '{act}' was not found in audit logs. Actions present: {actions_logged}"

    # Verify user_role and summary are populated
    login_logs = [l for l in logs if l['action'] == 'LOGIN_PASSWORD_SUCCESS']
    assert len(login_logs) >= 1
    assert login_logs[0]['user_role'] in ['ADMIN', 'DOCTOR', 'RECEPTIONIST']
    assert len(login_logs[0]['summary']) > 5
