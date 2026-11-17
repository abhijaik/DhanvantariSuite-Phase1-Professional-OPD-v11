import json
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.adapters.api.dependencies import get_db, require_role
from src.adapters.db.orm_models import AppointmentORM, ConsultationORM, InvoiceORM, PatientORM
from src.domain.models.user import User, UserRole

router = APIRouter(prefix="/api/reports", tags=["Doctor Reports"])


def _safe_json_list(raw: Optional[str]) -> list:
    if not raw:
        return []
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else []
    except Exception:
        return []


@router.get("/doctor")
def get_doctor_reports(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.DOCTOR, UserRole.DOCTOR_ALL])),
):
    """Return all 6 clinical and practice reports scoped to the doctor (or branch for DOCTOR_ALL)."""
    today = date.today()
    eff_end = end_date or today
    eff_start = start_date or (eff_end - timedelta(days=29))
    if eff_start > eff_end:
        eff_start, eff_end = eff_end, eff_start

    appt_q = db.query(AppointmentORM).filter(
        AppointmentORM.tenant_id == current_user.tenant_id,
        AppointmentORM.branch_id == current_user.branch_id,
        AppointmentORM.appointment_date >= eff_start,
        AppointmentORM.appointment_date <= eff_end,
    )
    if current_user.role == UserRole.DOCTOR:
        appt_q = appt_q.filter(AppointmentORM.doctor_id == current_user.id)

    appointments = appt_q.all()
    appt_ids = [a.id for a in appointments]

    # 1. OPD & Consultation Summary
    total_appointments = len(appointments)
    completed_count = sum(1 for a in appointments if a.status == "COMPLETED")
    cancelled_count = sum(1 for a in appointments if a.status == "CANCELLED")
    active_count = total_appointments - completed_count - cancelled_count
    new_visits = sum(1 for a in appointments if (a.visit_type or "").lower() == "new" and a.status != "CANCELLED")
    followup_visits = sum(1 for a in appointments if (a.visit_type or "").lower() != "new" and a.status != "CANCELLED")

    consult_type_counts = Counter(
        (a.consultation_type or "General") for a in appointments if a.status != "CANCELLED"
    )
    by_consultation_type = [
        {"type": k, "count": v} for k, v in consult_type_counts.most_common()
    ]

    # Consultations in date range (linked to appointments in range)
    consultations = []
    if appt_ids:
        consultations = (
            db.query(ConsultationORM)
            .filter(
                ConsultationORM.tenant_id == current_user.tenant_id,
                ConsultationORM.branch_id == current_user.branch_id,
                ConsultationORM.appointment_id.in_(appt_ids),
            )
            .all()
        )

    # 2. Follow-Up Due & Overdue List (all non-null follow_up_date for this doctor/branch)
    fu_q = (
        db.query(ConsultationORM, PatientORM)
        .join(PatientORM, ConsultationORM.patient_id == PatientORM.id)
        .filter(
            ConsultationORM.tenant_id == current_user.tenant_id,
            ConsultationORM.branch_id == current_user.branch_id,
            ConsultationORM.follow_up_date.isnot(None),
        )
    )
    if current_user.role == UserRole.DOCTOR:
        fu_q = fu_q.filter(ConsultationORM.doctor_id == current_user.id)
    fu_rows = fu_q.order_by(ConsultationORM.follow_up_date.asc()).all()

    follow_ups = []
    for c, p in fu_rows:
        fu_date = c.follow_up_date
        if fu_date < today:
            bucket = "OVERDUE"
        elif fu_date == today:
            bucket = "TODAY"
        else:
            bucket = "UPCOMING"
        follow_ups.append({
            "patient_id": p.id,
            "patient_name": p.full_name,
            "patient_number": p.patient_number,
            "mobile": p.mobile_normalized,
            "follow_up_date": fu_date.isoformat(),
            "diagnosis": c.diagnosis or "",
            "status_bucket": bucket,
        })

    # 3. Diagnosis & Symptom Trends
    diag_counts: Counter = Counter()
    sym_counts: Counter = Counter()
    med_counts: Counter = Counter()

    for c in consultations:
        diag = (c.diagnosis or "").strip()
        if diag:
            diag_counts[diag] += 1
        for s in _safe_json_list(c.symptoms):
            s_clean = str(s).strip()
            if s_clean:
                sym_counts[s_clean] += 1
        for item in _safe_json_list(c.prescription_json):
            if isinstance(item, dict):
                m_name = str(item.get("medicine_name") or "").strip()
                if m_name:
                    med_counts[m_name] += 1

    top_diagnoses = [{"name": k, "count": v} for k, v in diag_counts.most_common(20)]
    top_symptoms = [{"name": k, "count": v} for k, v in sym_counts.most_common(20)]

    # 4. Top Prescribed Medicines
    top_medicines = [{"medicine_name": k, "count": v} for k, v in med_counts.most_common(25)]

    # 5. My Consultation Revenue & Pending Dues
    invoices = []
    if appt_ids:
        invoices = (
            db.query(InvoiceORM)
            .filter(
                InvoiceORM.tenant_id == current_user.tenant_id,
                InvoiceORM.branch_id == current_user.branch_id,
                InvoiceORM.appointment_id.in_(appt_ids),
            )
            .all()
        )

    total_billed = sum((Decimal(inv.total_amount or 0) for inv in invoices), Decimal("0.00"))
    total_collected = sum((Decimal(inv.amount_paid or 0) for inv in invoices), Decimal("0.00"))
    total_due = sum((Decimal(inv.amount_due or 0) for inv in invoices), Decimal("0.00"))
    consultation_charges = sum((Decimal(inv.consultation_charges or 0) for inv in invoices), Decimal("0.00"))

    mode_totals: dict[str, dict] = {}
    status_totals: dict[str, dict] = {}
    for inv in invoices:
        m = inv.payment_mode or "CASH"
        if m not in mode_totals:
            mode_totals[m] = {"mode": m, "count": 0, "amount": Decimal("0.00")}
        mode_totals[m]["count"] += 1
        mode_totals[m]["amount"] += Decimal(inv.amount_paid or 0)

        st = inv.payment_status or "PENDING"
        if st not in status_totals:
            status_totals[st] = {"status": st, "count": 0, "amount": Decimal("0.00")}
        status_totals[st]["count"] += 1
        status_totals[st]["amount"] += Decimal(inv.total_amount or 0)

    # 6. Patient Referral Report
    ref_counts: Counter = Counter()
    for a in appointments:
        if a.status == "CANCELLED":
            continue
        r_type = (a.referred_by_type or "").strip()
        r_name = (a.referred_by_name or "").strip()
        if r_type or r_name:
            ref_counts[(r_type or "Other", r_name or "-")] += 1

    referrals = [
        {"referred_by_type": k[0], "referred_by_name": k[1], "count": v}
        for k, v in ref_counts.most_common()
    ]

    return {
        "start_date": eff_start.isoformat(),
        "end_date": eff_end.isoformat(),
        "opd_summary": {
            "total_appointments": total_appointments,
            "completed": completed_count,
            "cancelled": cancelled_count,
            "active_or_pending": active_count,
            "new_visits": new_visits,
            "followup_visits": followup_visits,
            "by_consultation_type": by_consultation_type,
        },
        "follow_ups": follow_ups,
        "diagnosis_trends": {
            "top_diagnoses": top_diagnoses,
            "top_symptoms": top_symptoms,
        },
        "top_medicines": top_medicines,
        "revenue_summary": {
            "total_invoices": len(invoices),
            "consultation_charges": float(consultation_charges),
            "total_billed": float(total_billed),
            "total_collected": float(total_collected),
            "total_due": float(total_due),
            "by_payment_mode": [
                {"mode": v["mode"], "count": v["count"], "amount": float(v["amount"])}
                for v in mode_totals.values()
            ],
            "by_payment_status": [
                {"status": v["status"], "count": v["count"], "amount": float(v["amount"])}
                for v in status_totals.values()
            ],
        },
        "referrals": referrals,
    }
