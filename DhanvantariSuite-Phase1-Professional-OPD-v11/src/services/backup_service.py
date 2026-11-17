import json
import os
import shutil
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from src.adapters.db.orm_models import (
    UserORM, PatientORM, AppointmentORM, ConsultationORM,
    InvoiceORM, VitalsConfigORM, AppointmentVitalsORM, SyncLogORM,
    ClinicSettingsORM, AuditLogORM, MedicineORM, PatientReportORM
)

BACKUP_ROOT = Path(__file__).resolve().parent.parent.parent / "backups"
REPORTS_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads" / "reports"

MODELS_ORDER = [
    ("users", UserORM),
    ("clinic_settings", ClinicSettingsORM),
    ("vitals_config", VitalsConfigORM),
    ("medicines", MedicineORM),
    ("patients", PatientORM),
    ("appointments", AppointmentORM),
    ("appointment_vitals", AppointmentVitalsORM),
    ("consultations", ConsultationORM),
    ("invoices", InvoiceORM),
    ("patient_reports", PatientReportORM),
    ("sync_logs", SyncLogORM),
    ("audit_logs", AuditLogORM),
]


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


class BackupService:
    def __init__(self, db: Session):
        self.db = db

    def create_backup(
        self,
        tenant_id: str,
        branch_id: str,
        backup_type: str = "MANUAL",
        created_by_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a complete portable backup archive (.dhanbackup).
        Contains serialized database snapshot (all tenant tables) + uploaded patient reports.
        """
        tenant_backup_dir = BACKUP_ROOT / tenant_id
        tenant_backup_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.utcnow()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"dhanvantari_{tenant_id}_{timestamp_str}.dhanbackup"
        final_archive_path = tenant_backup_dir / backup_filename

        db_dump: Dict[str, List[Dict[str, Any]]] = {}
        counts: Dict[str, int] = {}

        # 1. Export tables for this tenant
        for table_key, model_cls in MODELS_ORDER:
            query = self.db.query(model_cls)
            # Only filter by tenant_id if model has tenant_id column
            mapper = inspect(model_cls)
            if "tenant_id" in mapper.columns:
                query = query.filter(model_cls.tenant_id == tenant_id)

            records = query.all()
            table_data = []
            for r in records:
                row_dict = {}
                for col in mapper.columns:
                    val = getattr(r, col.key)
                    if isinstance(val, (datetime, date)):
                        row_dict[col.key] = val.isoformat()
                    else:
                        row_dict[col.key] = val
                table_data.append(row_dict)

            db_dump[table_key] = table_data
            counts[table_key] = len(table_data)

        manifest = {
            "version": "1.0",
            "app": "Dhanvantari Clinic ERP",
            "format": "dhanbackup",
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "created_at": now.isoformat(),
            "backup_type": backup_type,
            "created_by": created_by_user_id,
            "record_counts": counts
        }

        # 2. Package into a compressed ZIP (.dhanbackup)
        with zipfile.ZipFile(final_archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("database.json", json.dumps(db_dump, cls=DateTimeEncoder, indent=2))

            # Include uploaded patient reports files if any
            tenant_reports_dir = REPORTS_ROOT / tenant_id
            if tenant_reports_dir.exists():
                for root, _, files in os.walk(tenant_reports_dir):
                    for file in files:
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(tenant_reports_dir)
                        zf.write(file_path, arcname=f"reports/{rel_path}")

        file_size = final_archive_path.stat().st_size

        # 3. Rotate rolling automatic backups (keep last 7)
        if backup_type == "AUTO":
            self._prune_auto_backups(tenant_id, max_keep=7)

        return {
            "filename": backup_filename,
            "file_size_bytes": file_size,
            "created_at": now.isoformat(),
            "backup_type": backup_type,
            "record_counts": counts
        }

    def list_backups(self, tenant_id: str) -> List[Dict[str, Any]]:
        """List all available backups for a tenant."""
        tenant_backup_dir = BACKUP_ROOT / tenant_id
        if not tenant_backup_dir.exists():
            return []

        backups = []
        for file in sorted(tenant_backup_dir.glob("*.dhanbackup"), key=os.path.getmtime, reverse=True):
            try:
                stat = file.stat()
                # Read manifest from zip
                manifest_data = {}
                try:
                    with zipfile.ZipFile(file, "r") as zf:
                        if "manifest.json" in zf.namelist():
                            manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                except Exception:
                    pass

                backups.append({
                    "filename": file.name,
                    "file_size_bytes": stat.st_size,
                    "created_at": manifest_data.get("created_at") or datetime.utcfromtimestamp(stat.st_mtime).isoformat(),
                    "backup_type": manifest_data.get("backup_type", "UNKNOWN"),
                    "record_counts": manifest_data.get("record_counts", {})
                })
            except Exception:
                continue

        return backups

    def restore_backup(
        self,
        tenant_id: str,
        archive_path: Path
    ) -> Dict[str, Any]:
        """
        Restores clinic database and uploaded reports from a .dhanbackup archive.
        Safe against data loss; records are upserted or inserted.
        """
        if not zipfile.is_zipfile(archive_path):
            raise ValueError("Invalid backup file: Not a valid .dhanbackup archive.")

        with zipfile.ZipFile(archive_path, "r") as zf:
            if "manifest.json" not in zf.namelist() or "database.json" not in zf.namelist():
                raise ValueError("Corrupt backup file: Missing manifest.json or database.json.")

            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            db_dump = json.loads(zf.read("database.json").decode("utf-8"))

            backup_tenant = manifest.get("tenant_id")
            # If restoring to a fresh install where tenant_id matches or user allows cross-tenant import
            target_tenant = tenant_id

            restored_counts = {}

            # Restore database records in dependency order
            for table_key, model_cls in MODELS_ORDER:
                rows = db_dump.get(table_key, [])
                mapper = inspect(model_cls)
                pk_names = [col.key for col in mapper.primary_key]
                count = 0

                for row in rows:
                    # Overwrite tenant_id if tenant was changed/restored
                    if "tenant_id" in row and backup_tenant != target_tenant:
                        row["tenant_id"] = target_tenant

                    # Parse datetime/date fields back to objects
                    row_clean = {}
                    for k, v in row.items():
                        if k in mapper.columns:
                            col_type = mapper.columns[k].type.python_type
                            if v is not None:
                                if col_type is datetime:
                                    try:
                                        row_clean[k] = datetime.fromisoformat(v)
                                    except Exception:
                                        row_clean[k] = v
                                elif col_type is date:
                                    try:
                                        row_clean[k] = date.fromisoformat(v)
                                    except Exception:
                                        row_clean[k] = v
                                else:
                                    row_clean[k] = v
                            else:
                                row_clean[k] = None

                    # Check if record already exists by primary key
                    filter_kwargs = {pk: row_clean[pk] for pk in pk_names if pk in row_clean}
                    existing = None
                    if filter_kwargs:
                        existing = self.db.query(model_cls).filter_by(**filter_kwargs).first()

                    if existing:
                        # Update fields
                        for k, v in row_clean.items():
                            setattr(existing, k, v)
                    else:
                        obj = model_cls(**row_clean)
                        self.db.add(obj)
                    count += 1

                self.db.commit()
                restored_counts[table_key] = count

            # Restore uploaded report files
            tenant_reports_dir = REPORTS_ROOT / target_tenant
            tenant_reports_dir.mkdir(parents=True, exist_ok=True)
            files_restored = 0
            for item in zf.namelist():
                if item.startswith("reports/") and not item.endswith("/"):
                    rel = item[len("reports/"):]
                    target_file = tenant_reports_dir / rel
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(item) as src, open(target_file, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    files_restored += 1

        return {
            "status": "success",
            "restored_at": datetime.utcnow().isoformat(),
            "manifest": manifest,
            "restored_records": restored_counts,
            "restored_files_count": files_restored
        }

    def _prune_auto_backups(self, tenant_id: str, max_keep: int = 7):
        """Keep only the latest N auto-backups."""
        tenant_backup_dir = BACKUP_ROOT / tenant_id
        if not tenant_backup_dir.exists():
            return

        auto_backups = []
        for file in tenant_backup_dir.glob("*.dhanbackup"):
            try:
                with zipfile.ZipFile(file, "r") as zf:
                    if "manifest.json" in zf.namelist():
                        m = json.loads(zf.read("manifest.json").decode("utf-8"))
                        if m.get("backup_type") == "AUTO":
                            auto_backups.append((file, file.stat().st_mtime))
            except Exception:
                pass

        auto_backups.sort(key=lambda x: x[1], reverse=True)
        for file, _ in auto_backups[max_keep:]:
            try:
                file.unlink(missing_ok=True)
            except Exception:
                pass

    def check_and_run_auto_backup(self, tenant_id: str, branch_id: str) -> Optional[Dict[str, Any]]:
        """Periodic check: if no backup in past 24 hours, take one automatically."""
        backups = self.list_backups(tenant_id)
        if backups:
            last_dt_str = backups[0]["created_at"]
            try:
                last_dt = datetime.fromisoformat(last_dt_str.replace("Z", ""))
                delta = datetime.utcnow() - last_dt
                if delta.total_seconds() < 86400:  # Less than 24 hours
                    return None
            except Exception:
                pass

        # Trigger automatic backup
        return self.create_backup(tenant_id, branch_id, backup_type="AUTO")
