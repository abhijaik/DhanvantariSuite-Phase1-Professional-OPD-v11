from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from src.adapters.db.connection import init_db
from src.adapters.api import router_auth, router_patient, router_queue, router_consultation, router_billing, router_sync, router_vitals, router_settings

app = FastAPI(
    title="Clinic Management System (ERP)",
    version="1.0.0",
    description="Decoupled offline-first multi-tenant LAN clinic management system"
)

# CORS middleware to support Tauri / PyWebView loopback requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup hook to auto-initialize SQLite schema locally
@app.on_event("startup")
def on_startup():
    init_db()
    seed_data()

def seed_data():
    from src.adapters.db.connection import get_db_session
    from src.adapters.db.repositories import SQLAlchemyUserRepository
    from src.services.auth_service import AuthService
    from src.domain.models.user import UserRole
    
    with get_db_session() as db:
        user_repo = SQLAlchemyUserRepository(db)
        auth_service = AuthService(user_repo)
        
        test_users = [
            ("admin_user", "adminpass123", "Clinic Administrator", UserRole.ADMIN),
            ("receptionist_user", "receppass123", "Clinic Receptionist", UserRole.RECEPTIONIST),
            ("doctor_user", "docpass123", "Dr. Vivek Singh", UserRole.DOCTOR)
        ]
        
        for username, password, full_name, role in test_users:
            existing = user_repo.find_by_username(username, "local-clinic")
            if not existing:
                try:
                    auth_service.register_user(
                        tenant_id="local-clinic",
                        branch_id="branch-main",
                        username=username,
                        password=password,
                        full_name=full_name,
                        role=role,
                        can_collect_payment=True,
                        can_enter_vitals=True,
                        can_view_clinical_history=(role in [UserRole.ADMIN, UserRole.DOCTOR]),
                        can_edit_clinical_data=(role == UserRole.DOCTOR)
                    )
                    print(f"Seeded test user: {username} ({role.value})")
                except Exception as e:
                    print(f"Error seeding user {username}: {e}")

# Include Routers
app.include_router(router_auth.router)
app.include_router(router_patient.router)
app.include_router(router_queue.router)
app.include_router(router_consultation.router)
app.include_router(router_billing.router)
app.include_router(router_sync.router)
app.include_router(router_vitals.router)
app.include_router(router_settings.router)

# Mount static directory for frontend assets
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/ui/", status_code=307)

