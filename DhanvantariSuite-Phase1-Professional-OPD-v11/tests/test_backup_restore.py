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
    auth.register_user("local-clinic", "branch-main", "admin_user", "adminpass123", "Admin User", UserRole.ADMIN, mobile="9800000020")
    auth.register_user("local-clinic", "branch-main", "doctor_user", "docpass123", "Dr. Doctor", UserRole.DOCTOR, mobile="9800000021")
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


def test_backup_and_restore_flow(client):
    admin_h = get_auth_header(client, "admin_user", "adminpass123")
    doc_h = get_auth_header(client, "doctor_user", "docpass123")

    # 1. Register a test patient
    pat_res = client.post("/api/patients/register", json={
        "full_name": "Suresh Raina",
        "date_of_birth": "1986-11-27",
        "age": 38,
        "gender": "Male",
        "mobile": "9812345678",
        "address": "Ghaziabad UP"
    }, headers=admin_h)
    assert pat_res.status_code == 200
    pat_id = pat_res.json()["id"]

    # 2. Upload a test report
    dummy_pdf = io.BytesIO(b"%PDF-1.4 sample diagnostic test report")
    upload_res = client.post(
        "/api/patient-reports/upload-file",
        data={
            "patient_id": pat_id,
            "report_title": "X-Ray Knee AP/Lat",
            "report_type": "Radiology / X-Ray",
            "source_type": "FILE_UPLOAD",
            "notes": "Mild osteophyte"
        },
        files={"file": ("knee_xray.pdf", dummy_pdf, "application/pdf")},
        headers=doc_h
    )
    assert upload_res.status_code == 200

    # 3. Create a manual backup
    bk_res = client.post("/api/backup/create", headers=admin_h)
    assert bk_res.status_code == 200
    bk_data = bk_res.json()
    assert "filename" in bk_data
    assert bk_data["filename"].endswith(".dhanbackup")
    assert bk_data["record_counts"]["patients"] >= 1
    assert bk_data["record_counts"]["patient_reports"] >= 1
    filename = bk_data["filename"]

    # 4. List backups
    list_res = client.get("/api/backup/list", headers=admin_h)
    assert list_res.status_code == 200
    backups = list_res.json()
    assert any(b["filename"] == filename for b in backups)

    # 5. Download the backup
    dl_res = client.get(f"/api/backup/download/{filename}", headers=admin_h)
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 0
    backup_bytes = dl_res.content

    # 6. Test restore from the backup
    restore_res = client.post(
        "/api/backup/restore",
        files={"file": (filename, io.BytesIO(backup_bytes), "application/octet-stream")},
        headers=admin_h
    )
    assert restore_res.status_code == 200
    restored_info = restore_res.json()
    assert restored_info["status"] == "success"
    assert restored_info["restored_records"]["patients"] >= 1

    # 7. Check automatic backup check endpoint
    auto_res = client.post("/api/backup/auto-check", headers=admin_h)
    assert auto_res.status_code == 200
    # Because backup was just made, auto_backup_created should be False
    assert auto_res.json()["auto_backup_created"] is False
