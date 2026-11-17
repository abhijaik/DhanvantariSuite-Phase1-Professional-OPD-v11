import io
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

@pytest.fixture(name="client", scope="module")
def fixture_client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    auth = AuthService(SQLAlchemyUserRepository(db))
    auth.register_user("local-clinic", "branch-main", "admin_user", "adminpass123", "Admin User", UserRole.ADMIN, mobile="9800000010")
    auth.register_user("local-clinic", "branch-main", "doctor_user", "docpass123", "Dr. Doctor", UserRole.DOCTOR, mobile="9800000011")
    auth.register_user("local-clinic", "branch-main", "receptionist_user", "receppass123", "Recep User", UserRole.RECEPTIONIST, mobile="9800000012")
    db.commit()
    db.close()

    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)


def get_auth_header(client: TestClient, username: str, password: str):
    res = client.post("/api/auth/login", data={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": "local-clinic", "X-Branch-ID": "branch-main"}


def test_patient_reports_flow(client):
    admin_h = get_auth_header(client, "admin_user", "adminpass123")
    doc_h = get_auth_header(client, "doctor_user", "docpass123")

    # 1. Register a test patient
    pat_res = client.post("/api/patients/register", json={
        "full_name": "Rohan Deshmukh",
        "date_of_birth": "1990-05-15",
        "age": 34,
        "gender": "Male",
        "mobile": "9876543210",
        "address": "Pune Maharashtra"
    }, headers=admin_h)
    assert pat_res.status_code == 200
    pat_id = pat_res.json()["id"]

    # 2. Upload a PDF report file as Doctor
    dummy_pdf = io.BytesIO(b"%PDF-1.4 test lab report content")
    upload_res = client.post(
        "/api/patient-reports/upload-file",
        data={
            "patient_id": pat_id,
            "report_title": "Blood Test CBC",
            "report_type": "Lab Report",
            "source_type": "FILE_UPLOAD",
            "notes": "Hemoglobin slightly low"
        },
        files={"file": ("cbc_test.pdf", dummy_pdf, "application/pdf")},
        headers=doc_h
    )
    assert upload_res.status_code == 200
    rep1 = upload_res.json()
    assert rep1["report_title"] == "Blood Test CBC"
    assert rep1["source_type"] == "FILE_UPLOAD"
    assert rep1["file_name"] == "cbc_test.pdf"
    rep1_id = rep1["id"]

    # 3. Attach a Google Drive Link report
    drive_res = client.post(
        "/api/patient-reports/link",
        json={
            "patient_id": pat_id,
            "report_title": "MRI Spine Scan",
            "report_type": "Radiology / X-Ray",
            "source_type": "GOOGLE_DRIVE",
            "external_url": "https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I0J/view?usp=sharing",
            "notes": "L4-L5 disc bulge"
        },
        headers=doc_h
    )
    assert drive_res.status_code == 200
    rep2 = drive_res.json()
    assert rep2["source_type"] == "GOOGLE_DRIVE"
    assert "drive.google.com" in rep2["external_url"]
    rep2_id = rep2["id"]

    # 4. List reports for patient
    list_res = client.get(f"/api/patient-reports/patient/{pat_id}", headers=doc_h)
    assert list_res.status_code == 200
    reports = list_res.json()
    assert len(reports) >= 2
    titles = [r["report_title"] for r in reports]
    assert "Blood Test CBC" in titles
    assert "MRI Spine Scan" in titles

    # 5. Download the uploaded file
    dl_res = client.get(f"/api/patient-reports/{rep1_id}/file", headers=doc_h)
    assert dl_res.status_code == 200
    assert b"%PDF-1.4" in dl_res.content

    # 6. Delete a report
    del_res = client.delete(f"/api/patient-reports/{rep2_id}", headers=doc_h)
    assert del_res.status_code == 200

    # 7. Verify deletion
    list_res2 = client.get(f"/api/patient-reports/patient/{pat_id}", headers=doc_h)
    assert list_res2.status_code == 200
    remaining_ids = [r["id"] for r in list_res2.json()]
    assert rep2_id not in remaining_ids
    assert rep1_id in remaining_ids
