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

        # Seed standard OPD medicines
        try:
            import uuid
            from datetime import datetime
            from src.adapters.db.repositories import SQLAlchemyMedicineRepository
            from src.domain.models.medicine import Medicine

            med_repo = SQLAlchemyMedicineRepository(db)
            starter_meds = [
                ("Paracetamol 650mg", "Tablet", "1-0-1", "3 Days", "After Food", "Take for fever or pain"),
                ("Paracetamol 500mg", "Tablet", "1-0-1", "3 Days", "After Food", "For mild fever or headache"),
                ("Dolo 650", "Tablet", "1-0-1", "3 Days", "After Food", "For body pain & fever"),
                ("Amoxicillin 500mg", "Capsule", "1-0-1", "5 Days", "After Food", "Complete full antibiotic course"),
                ("Azithromycin 500mg", "Tablet", "1-0-0", "3 Days", "After Food", "Take once daily for 3 days"),
                ("Ciprofloxacin 500mg", "Tablet", "1-0-1", "5 Days", "After Food", "Take after meals"),
                ("Pantoprazole 40mg", "Tablet", "1-0-0", "5 Days", "Empty Stomach", "Take early morning 30 mins before breakfast"),
                ("Omeprazole 20mg", "Capsule", "1-0-0", "7 Days", "Empty Stomach", "Take before morning breakfast"),
                ("Ranitidine 150mg", "Tablet", "1-0-1", "5 Days", "Before Food", "Take before meals for acidity"),
                ("Cetirizine 10mg", "Tablet", "0-0-1", "3 Days", "Bedtime", "Take at bedtime for allergy"),
                ("Montelukast + Levocetirizine", "Tablet", "0-0-1", "5 Days", "Bedtime", "Take at bedtime for allergic rhinitis/cough"),
                ("Metformin 500mg", "Tablet", "1-0-1", "1 Month", "With Food", "Take with meals"),
                ("Amlodipine 5mg", "Tablet", "1-0-0", "1 Month", "After Food", "Take every morning"),
                ("Telmisartan 40mg", "Tablet", "1-0-0", "1 Month", "After Food", "Take once daily in morning"),
                ("Atorvastatin 10mg", "Tablet", "0-0-1", "1 Month", "Bedtime", "Take at night for lipid control"),
                ("Ibuprofen 400mg", "Tablet", "1-0-1", "3 Days", "After Food", "Take with plenty of water after meals"),
                ("Diclofenac 50mg", "Tablet", "1-0-1", "3 Days", "After Food", "Take after food for acute pain"),
                ("ORS Sachet", "Powder", "1-1-1", "2 Days", "Anytime", "Dissolve 1 sachet in 1 liter clean water"),
                ("Cough Syrup (Dextromethorphan)", "Syrup", "1-1-1", "5 Days", "After Food", "Take 5ml after food"),
                ("Multivitamin & Minerals", "Tablet", "0-1-0", "15 Days", "After Food", "Take once daily after lunch"),
                ("Vitamin C 500mg", "Chewable", "0-1-0", "15 Days", "After Food", "Chew 1 tablet after lunch"),
                ("Calcium + Vitamin D3", "Tablet", "0-1-0", "1 Month", "After Food", "Take once daily with water"),
                ("B-Complex with Zinc", "Capsule", "0-1-0", "15 Days", "After Food", "Take once daily after lunch"),
                ("Domperidone 10mg", "Tablet", "1-0-1", "3 Days", "Before Food", "Take 15 mins before food for nausea"),
                ("Ondansetron 4mg", "Tablet", "1-0-1", "2 Days", "Before Food", "Take for nausea/vomiting"),
                ("Ofloxacin + Ornidazole", "Tablet", "1-0-1", "5 Days", "After Food", "Take after meals for loose motion")
            ]
            added = 0
            for name, form, timing, duration, food, notes in starter_meds:
                if not med_repo.find_by_name(name, "local-clinic"):
                    med = Medicine(
                        id=str(uuid.uuid4()),
                        tenant_id="local-clinic",
                        name=name,
                        dosage_form=form,
                        default_timing=timing,
                        default_duration=duration,
                        default_food_relation=food,
                        instructions=notes,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    med_repo.save(med)
                    added += 1
            if added:
                print(f"Seeded {added} new OPD medicines.")
        except Exception as e:
            print(f"Error seeding initial medicines: {e}")

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

