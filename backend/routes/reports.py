from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from typing import Optional
import io
import csv
from ..database import get_db
from ..models import Invoice, Payment, User
from ..dependencies import get_current_user
from ..services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/aging")
def get_aging(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ReportService.get_aging_report(db, current_user.business_id)

@router.get("/reconciliation")
def get_reconciliation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ReportService.get_reconciliation_summary(db, current_user.business_id)

@router.get("/ledger/{customer_id}")
def get_ledger(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return ReportService.get_customer_ledger(db, current_user.business_id, customer_id)

@router.get("/export/{report_type}")
def export_csv(
    report_type: str,
    customer_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "aging":
        data = ReportService.get_aging_report(db, current_user.business_id)
        writer.writerow(["Customer Name", "Company", "Phone", "Current (0-30d)", "Overdue 31-60d", "Overdue 61-90d", "Overdue 90+d", "Total Due", "Risk Level"])
        for c in data["customers"]:
            writer.writerow([
                c["customer_name"], c["company_name"], c["phone"],
                c["current"], c["days_31_60"], c["days_61_90"], c["days_90_plus"],
                c["total_due"], c["risk_level"]
            ])
        filename = "FinSight_Aging_Report.csv"

    elif report_type == "ledger" and customer_id:
        data = ReportService.get_customer_ledger(db, current_user.business_id, customer_id)
        writer.writerow(["Date", "Transaction Type", "Reference", "Description", "Debit (Invoice)", "Credit (Payment)", "Running Balance", "Status"])
        for row in data.get("statement", []):
            writer.writerow([
                row["date"], row["type"], row["reference"], row["description"],
                row["debit"], row["credit"], row["running_balance"], row["status"]
            ])
        filename = f"Customer_Ledger_{customer_id}.csv"

    elif report_type == "invoices":
        invoices = db.query(Invoice).filter(Invoice.business_id == current_user.business_id).all()
        writer.writerow(["Invoice #", "Customer", "Issue Date", "Due Date", "Total (PKR)", "Paid Amount", "Balance Due", "Status"])
        for inv in invoices:
            writer.writerow([
                inv.invoice_number, inv.customer.name if inv.customer else "",
                inv.issue_date, inv.due_date, inv.total_amount, inv.paid_amount, inv.balance_due, inv.status
            ])
        filename = "FinSight_Invoices_Report.csv"

    else:
        payments = db.query(Payment).filter(Payment.business_id == current_user.business_id).all()
        writer.writerow(["Payment #", "Customer", "Date", "Amount (PKR)", "Unallocated Amount", "Method", "Reference", "Status"])
        for p in payments:
            writer.writerow([
                p.payment_number, p.customer.name if p.customer else "",
                p.payment_date, p.amount, p.unallocated_amount, p.payment_method, p.reference_number or "", p.status
            ])
        filename = "FinSight_Payments_Report.csv"

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
