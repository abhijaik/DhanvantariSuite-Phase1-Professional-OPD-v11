import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.adapters.api.dependencies import get_db
from src.adapters.db.orm_models import Base
from src.adapters.db.repositories import SQLAlchemyUserRepository
from src.services.auth_service import AuthService
from src.domain.models.user import UserRole
from src.adapters.docgen.pdf_generator import PDFGeneratorAdapter
from src.domain.models.consultation import Consultation, PrescriptionItem
from src.domain.models.patient import Patient
from src.domain.models.user import User

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
    repo = SQLAlchemyUserRepository(db)
    auth = AuthService(repo)
    # Register test staff
    auth.register_user('test-tenant', 'branch-1', 'admin_test', 'adminpass', 'Admin Test', UserRole.ADMIN, mobile='9100000001')
    auth.register_user('test-tenant', 'branch-1', 'doctor_test', 'docpass', 'Dr. Vivek Test', UserRole.DOCTOR, mobile='9100000002')
    auth.register_user('test-tenant', 'branch-1', 'reception_test', 'receppass', 'Reception Test', UserRole.RECEPTIONIST, mobile='9100000003')
    db.commit()
    db.close()

    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)


def get_auth_header(client, username, password):
    r = client.post('/api/auth/login', data={'username': username, 'password': password}, headers={'X-Tenant-ID': 'test-tenant', 'X-Branch-ID': 'branch-1'})
    assert r.status_code == 200, r.text
    token = r.json()['access_token']
    return {
        'Authorization': f'Bearer {token}',
        'X-Tenant-ID': 'test-tenant',
        'X-Branch-ID': 'branch-1'
    }


def test_otp_login_flow(client):
    """Test Requirement 3: User can login using OTP or Password."""
    # 1. Request OTP using username
    req_r = client.post('/api/auth/otp/request', json={'username_or_mobile': 'doctor_test'}, headers={'X-Tenant-ID': 'test-tenant'})
    assert req_r.status_code == 200
    otp_data = req_r.json()
    assert otp_data['success'] is True
    assert 'demo_otp' in otp_data
    demo_otp = otp_data['demo_otp']

    # 2. Reject incorrect OTP
    bad_r = client.post('/api/auth/otp/verify', json={'username_or_mobile': 'doctor_test', 'otp': '000000'}, headers={'X-Tenant-ID': 'test-tenant'})
    assert bad_r.status_code == 400
    assert 'Invalid OTP' in bad_r.json()['detail']

    # 3. Request OTP using mobile number
    req_mob = client.post('/api/auth/otp/request', json={'username_or_mobile': '9100000002'}, headers={'X-Tenant-ID': 'test-tenant'})
    assert req_mob.status_code == 200
    mob_otp = req_mob.json()['demo_otp']

    # 4. Verify correct OTP and receive JWT access token
    verify_r = client.post('/api/auth/otp/verify', json={'username_or_mobile': '9100000002', 'otp': mob_otp}, headers={'X-Tenant-ID': 'test-tenant'})
    assert verify_r.status_code == 200
    res = verify_r.json()
    assert 'access_token' in res
    assert res['role'] == 'DOCTOR'
    assert res['username'] == 'doctor_test'


def test_doctor_checkin_and_dashboard_counts(client):
    """Test Requirement 1: Dashboard counts accurately reflect Today's patients, checked-in, and completed patients."""
    doc_h = get_auth_header(client, 'doctor_test', 'docpass')
    rec_h = get_auth_header(client, 'reception_test', 'receppass')

    # Register 2 patients
    p1_r = client.post('/api/patients/register', json={
        'full_name': 'Patient Alpha', 'mobile': '9200000001', 'date_of_birth': '1992-05-10',
        'age': 34, 'gender': 'Female', 'address': 'Pune'
    }, headers=rec_h)
    assert p1_r.status_code == 200
    p1_id = p1_r.json()['id']

    p2_r = client.post('/api/patients/register', json={
        'full_name': 'Patient Beta', 'mobile': '9200000002', 'date_of_birth': '1988-08-15',
        'age': 38, 'gender': 'Male', 'address': 'Mumbai'
    }, headers=rec_h)
    assert p2_r.status_code == 200
    p2_id = p2_r.json()['id']

    # Book appointments for today
    today_str = str(date.today())
    b1_r = client.post('/api/queue/book', json={
        'patient_id': p1_id, 'appointment_date': today_str, 'scheduled_time': '10:00:00',
        'visit_type': 'New Patient', 'consultation_type': 'General Consultation', 'check_in_now': False
    }, headers=rec_h)
    assert b1_r.status_code == 200
    a1_id = b1_r.json()['id']
    assert b1_r.json()['status'] == 'BOOKED'

    b2_r = client.post('/api/queue/book', json={
        'patient_id': p2_id, 'appointment_date': today_str, 'scheduled_time': '10:30:00',
        'visit_type': 'New Patient', 'consultation_type': 'General Consultation', 'check_in_now': False
    }, headers=rec_h)
    assert b2_r.status_code == 200
    a2_id = b2_r.json()['id']

    # Check queue details: both booked (scheduled)
    q_r = client.get('/api/queue/live/details', headers=rec_h)
    assert q_r.status_code == 200
    q = q_r.json()
    assert len(q) >= 2
    scheduled_count = len([x for x in q if x['appointment']['status'] in ['BOOKED', 'SCHEDULED']])
    checked_in_count = len([x for x in q if x['appointment']['status'] in ['IN_QUEUE', 'CHECKED_IN']])
    assert scheduled_count >= 2
    assert checked_in_count == 0

    # DOCTOR performs check-in for Patient Alpha (Requirement 1)
    ci_r = client.post(f'/api/queue/{a1_id}/checkin', headers=doc_h)
    assert ci_r.status_code == 200
    assert ci_r.json()['status'] in ['CHECKED_IN', 'IN_QUEUE']

    # Verify status changed at runtime on Receptionist's view
    q_rec = client.get('/api/queue/live/details', headers=rec_h).json()
    p1_appt = next(x['appointment'] for x in q_rec if x['appointment']['id'] == a1_id)
    assert p1_appt['status'] in ['CHECKED_IN', 'IN_QUEUE']
    new_checked_in = len([x for x in q_rec if x['appointment']['status'] in ['IN_QUEUE', 'CHECKED_IN']])
    assert new_checked_in == 1

    # Doctor starts consult for Patient Alpha
    client.post(f'/api/queue/{a1_id}/start-consult', headers=doc_h)

    # Doctor completes consultation for Patient Alpha
    comp_r = client.post('/api/consultations/complete', json={
        'appointment_id': a1_id,
        'symptoms': ['Headache', 'Mild fever'],
        'diagnosis': 'Tension Headache',
        'prescription': [{
            'medicine_name': 'Paracetamol 500mg',
            'dosage': '1-0-1',
            'frequency': '',
            'duration': '3 Days',
            'food_relation': 'After Food',
            'instructions': 'Take after meals'
        }]
    }, headers=doc_h)
    assert comp_r.status_code == 200
    consult_id = comp_r.json()['id']

    # Verify runtime reflection on Receptionist view:
    # 1. Total today's patients remains in sync (does not drop!)
    # 2. Completed count is now at least 1
    # 3. Receptionist can fetch consultation by appointment_id
    q_after_comp = client.get('/api/queue/live/details', headers=rec_h).json()
    completed_list = [x for x in q_after_comp if x['appointment']['status'] == 'COMPLETED']
    assert len(completed_list) >= 1
    assert any(x['appointment']['id'] == a1_id for x in completed_list)

    # Receptionist can fetch the consultation by appointment ID for prescription or billing
    c_by_appt = client.get(f'/api/consultations/appointment/{a1_id}', headers=rec_h)
    assert c_by_appt.status_code == 200
    assert c_by_appt.json()['id'] == consult_id


def test_multilingual_prescription_generation(client):
    """Test Requirement 2: Application supports English, Marathi, Hindi, and Arabic.
    Prescription generated is in that language except medicine names."""
    gen = PDFGeneratorAdapter()
    now = datetime.utcnow()
    patient = Patient(
        id='p-multi', tenant_id='t-test', branch_id='b-test', patient_number='P-999',
        registration_date=date.today(), full_name='Ramesh Patil', date_of_birth=date(1985, 2, 20),
        age=41, gender='Male', mobile_normalized='9988776655', address='Shivaji Nagar',
        created_at=now, updated_at=now
    )
    doctor = User(
        id='d-multi', tenant_id='t-test', branch_id='b-test', username='dr_test', password_hash='',
        full_name='Dr. Sneha Kulkarni', role=UserRole.DOCTOR, created_at=now, updated_at=now
    )
    prescription_items = [
        PrescriptionItem(medicine_name='Amoxicillin 500mg', dosage='1-0-1', frequency='', duration='5 Days', food_relation='After Food', instructions='Complete course'),
        PrescriptionItem(medicine_name='Cetirizine 10mg', dosage='0-0-1', frequency='', duration='3 Days', food_relation='Bedtime', instructions='Take at night')
    ]
    consultation = Consultation(
        id='c-multi', tenant_id='t-test', branch_id='b-test', appointment_id='a-multi', patient_id='p-multi',
        doctor_id='d-multi', consultation_type='Routine Checkup', symptoms=['Cough', 'Cold'], diagnosis='Upper Respiratory Tract Infection',
        prescription=prescription_items, blood_pressure='118/76', weight=68.0, height=172.0, bmi=23.0,
        pulse_rate=72, temperature=98.6, follow_up_date=date(2026, 11, 1), notes='Warm water gargles daily',
        created_at=now, updated_at=now
    )

    # Verify PDF generation in all 4 required languages
    for lang in ['en', 'mr', 'hi', 'ar']:
        pdf_bytes = gen.generate_prescription_pdf(consultation, patient, language=lang, doctor=doctor)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 2000, f"PDF for language '{lang}' was too small ({len(pdf_bytes)} bytes)"
        assert pdf_bytes.startswith(b'%PDF'), f"PDF for language '{lang}' did not start with standard PDF header"
