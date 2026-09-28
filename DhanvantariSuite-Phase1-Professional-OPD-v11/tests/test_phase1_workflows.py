import pytest
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

engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def override_get_db():
    db=Session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback(); raise
    finally:
        db.close()
app.dependency_overrides[get_db]=override_get_db

@pytest.fixture(scope='module')
def client():
    Base.metadata.create_all(bind=engine)
    db=Session()
    repo=SQLAlchemyUserRepository(db); auth=AuthService(repo)
    for u,p,n,r in [('admin_user','adminpass123','Admin',UserRole.ADMIN),('receptionist_user','receppass123','Reception',UserRole.RECEPTIONIST),('doctor_user','docpass123','Dr. First',UserRole.DOCTOR)]:
        auth.register_user('local-clinic','branch-main',u,p,n,r)
    db.commit(); db.close()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

def login(client, user, password):
    r=client.post('/api/auth/login', data={'username':user,'password':password})
    assert r.status_code==200, r.text
    d=r.json(); return {'Authorization':f"Bearer {d['access_token']}"}, d

def patient_payload(name, mobile):
    return {'full_name':name,'mobile':mobile,'date_of_birth':'1995-08-20','age':31,'gender':'Female','address':'Test'}

def test_single_doctor_doctor_flow(client):
    h,_=login(client,'doctor_user','docpass123')
    r=client.post('/api/patients/register-visit',json={**patient_payload('Single Doctor Patient','9000000001'),'visit_type':'New Patient','consultation_type':'Gynecology Consultation','check_in_now':True},headers=h)
    assert r.status_code==200,r.text
    d=r.json(); assert d['multi_doctor'] is False; assert d['appointment']['queue_token']==''; assert d['appointment']['status']=='CONSULTING'


def test_reception_single_doctor_does_not_start_clinical_consultation(client):
    h,_=login(client,'receptionist_user','receppass123')
    r=client.post('/api/patients/register-visit',json={**patient_payload('Reception Single','9000000002'),'visit_type':'New Patient','consultation_type':'Gynecology Consultation','check_in_now':True},headers=h)
    assert r.status_code==200,r.text
    d=r.json(); assert d['multi_doctor'] is False; assert d['appointment']['queue_token']==''; assert d['appointment']['status']=='BOOKED'


def test_multi_doctor_assignment_and_authorization(client):
    ah,_=login(client,'admin_user','adminpass123')
    add=client.post('/api/auth/register',json={'username':'doctor2','password':'doc2pass','full_name':'Dr. Second','role':'DOCTOR'},headers=ah)
    assert add.status_code==200,add.text
    rh,_=login(client,'receptionist_user','receppass123')
    r=client.post('/api/patients/register-visit',json={**patient_payload('Hospital Patient','9000000003'),'doctor_id':add.json()['id'],'visit_type':'New Patient','consultation_type':'Gynecology Consultation','check_in_now':True},headers=rh)
    assert r.status_code==200,r.text
    d=r.json(); assert d['multi_doctor'] is True; assert d['appointment']['queue_token'].startswith('T-'); assert d['appointment']['status']=='IN_QUEUE'
    # Receptionist cannot start consultation
    bad=client.post(f"/api/queue/{d['appointment']['id']}/start-consult",headers=rh)
    assert bad.status_code==403


def test_followup_creates_new_visit_not_duplicate(client):
    h,_=login(client,'doctor_user','docpass123')
    p=client.post('/api/patients/register',json=patient_payload('Followup Patient','9000000004'),headers=h)
    assert p.status_code==200
    pid=p.json()['id']
    f=client.post(f'/api/patients/{pid}/start-visit',json={'visit_type':'Follow-Up','consultation_type':'Follow-up Consultation','check_in_now':True},headers=h)
    assert f.status_code==200,f.text
    assert f.json()['patient']['id']==pid
    assert f.json()['appointment']['queue_token']==''
    dup=client.post('/api/patients/register',json=patient_payload('Duplicate','9000000004'),headers=h)
    assert dup.status_code in (400,409)


def test_receptionist_vitals_can_be_authorized_and_doctor_consumes_them(client):
    rh,_=login(client,'receptionist_user','receppass123')
    # use an existing appointment from the current queue
    q=client.get('/api/queue/live/details',headers=rh)
    assert q.status_code==200
    target=next(x for x in q.json() if x['appointment']['patient_id'])
    v=client.post('/api/vitals/record',json={'appointment_id':target['appointment']['id'],'blood_pressure':'120/80','weight':70,'height':175,'pulse':72},headers=rh)
    assert v.status_code==200,v.text
    assert v.json()['bmi'] is not None


def test_appointment_booking_and_consultation_pdf_history(client):
    from datetime import date, timedelta
    dh, duser = login(client, 'doctor_user', 'docpass123')
    rh, _ = login(client, 'receptionist_user', 'receppass123')

    # 1. Past date booking rejection
    past_date = (date.today() - timedelta(days=2)).isoformat()
    future_date = (date.today() + timedelta(days=1)).isoformat()

    p = client.post('/api/patients/register', json=patient_payload('Appt Patient', '9000000099'), headers=dh)
    assert p.status_code == 200
    pid = p.json()['id']

    past_res = client.post('/api/queue/book', json={
        'patient_id': pid,
        'appointment_date': past_date,
        'scheduled_time': '10:00:00',
        'visit_type': 'New Patient',
        'consultation_type': 'Gynecology Consultation'
    }, headers=dh)
    assert past_res.status_code == 400
    assert 'past' in past_res.json()['detail'].lower()

    # 2. Future date booking and booked slots check
    book_res = client.post('/api/queue/book', json={
        'patient_id': pid,
        'appointment_date': future_date,
        'scheduled_time': '14:30:00',
        'visit_type': 'New Patient',
        'consultation_type': 'Gynecology Consultation'
    }, headers=dh)
    assert book_res.status_code == 200

    slots_res = client.get(f'/api/queue/booked-slots?appointment_date={future_date}', headers=dh)
    assert slots_res.status_code == 200
    assert '14:30' in slots_res.json()['booked_slots']

    # 3. New Patient in Today's OPD is Save Only (check_in_now: False -> BOOKED)
    np_res = client.post('/api/patients/register-visit', json={
        **patient_payload('OPD Save Patient', '9000000098'),
        'visit_type': 'New Patient',
        'consultation_type': 'Gynecology Consultation',
        'doctor_id': duser['user_id'],
        'check_in_now': False
    }, headers=rh)
    assert np_res.status_code == 200, np_res.text
    saved_appt = np_res.json()['appointment']
    assert saved_appt['status'] == 'BOOKED'

    # 4. Reception checks in patient, then Doctor starts consultation
    cin_res = client.post(f"/api/queue/{saved_appt['id']}/checkin", headers=rh)
    assert cin_res.status_code == 200

    start_res = client.post(f"/api/queue/{saved_appt['id']}/start-consult", headers=dh)
    assert start_res.status_code == 200

    comp_res = client.post('/api/consultations/complete', json={
        'appointment_id': saved_appt['id'],
        'symptoms': ['Dysmenorrhea'],
        'diagnosis': 'Pelvic Congestion',
        'prescription': [{
            'medicine_name': 'Tab Drotaverine',
            'dosage': '1 tab',
            'frequency': 'Twice daily',
            'duration': '3 days',
            'food_relation': 'After food',
            'instructions': 'SOS'
        }],
        'blood_pressure': '120/80',
        'notes': 'Follow up if no relief.'
    }, headers=dh)
    assert comp_res.status_code == 200
    cid = comp_res.json()['id']

    # Header auth PDF print
    pdf_hdr = client.get(f'/api/consultations/{cid}/print?lang=en', headers=dh)
    assert pdf_hdr.status_code == 200
    assert pdf_hdr.content.startswith(b'%PDF')

    # Query param token PDF print
    pdf_token = client.get(f"/api/consultations/{cid}/print?lang=en&token={duser['access_token']}")
    assert pdf_token.status_code == 200
    assert pdf_token.content.startswith(b'%PDF')

    # 5. Doctor Patient History option
    hist_res = client.get(f'/api/consultations/patient/{pid}/history', headers=dh)
    assert hist_res.status_code == 200
    hist_save = client.get(f"/api/consultations/patient/{np_res.json()['patient']['id']}/history", headers=dh)
    assert hist_save.status_code == 200
    records = hist_save.json()
    assert len(records) >= 1
    assert records[0]['diagnosis'] == 'Pelvic Congestion'
    assert records[0]['prescription'][0]['medicine_name'] == 'Tab Drotaverine'
