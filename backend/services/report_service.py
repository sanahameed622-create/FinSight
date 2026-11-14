from sqlalchemy.orm import Session
from datetime import date
from typing import Dict, Any, List
from ..models import Invoice, Payment, Customer

class ReportService:

    @staticmethod
    def get_aging_report(db: Session, business_id: int) -> Dict[str, Any]:
        """Generate Accounts Receivable Aging Report broken down by standard aging buckets."""
        today = date.today()
        customers = db.query(Customer).filter(Customer.business_id == business_id).all()

        customer_aging = []
        grand_total_current = 0.0
        grand_total_30 = 0.0
        grand_total_60 = 0.0
        grand_total_90 = 0.0
        grand_total_due = 0.0

        for cust in customers:
            open_invoices = db.query(Invoice).filter(
                Invoice.customer_id == cust.id,
                Invoice.status.in_(["Issued", "Partially Paid", "Overdue"]),
                Invoice.balance_due > 0
            ).all()

            current = 0.0    # Not due yet or 0-30 days
            bucket_31_60 = 0.0
            bucket_61_90 = 0.0
            bucket_90_plus = 0.0
            cust_total_due = 0.0

            for inv in open_invoices:
                balance = inv.balance_due
                cust_total_due += balance

                if inv.due_date >= today:
                    current += balance
                else:
                    overdue_days = (today - inv.due_date).days
                    if overdue_days <= 30:
                        current += balance
                    elif overdue_days <= 60:
                        bucket_31_60 += balance
                    elif overdue_days <= 90:
                        bucket_61_90 += balance
                    else:
                        bucket_90_plus += balance

            if cust_total_due > 0 or cust.current_balance > 0:
                customer_aging.append({
                    "customer_id": cust.id,
                    "customer_name": cust.name,
                    "company_name": cust.company_name or cust.name,
                    "phone": cust.phone,
                    "current": round(current, 2),
                    "days_31_60": round(bucket_31_60, 2),
                    "days_61_90": round(bucket_61_90, 2),
                    "days_90_plus": round(bucket_90_plus, 2),
                    "total_due": round(cust_total_due, 2),
                    "credit_limit": cust.credit_limit,
                    "risk_level": "High" if bucket_90_plus > 0 or bucket_61_90 > 50000 else ("Medium" if bucket_31_60 > 0 else "Low")
                })

                grand_total_current += current
                grand_total_30 += bucket_31_60
                grand_total_60 += bucket_61_90
                grand_total_90 += bucket_90_plus
                grand_total_due += cust_total_due

        # Sort customers by total due descending
        customer_aging.sort(key=lambda x: x["total_due"], reverse=True)

        return {
            "report_date": today.isoformat(),
            "summary": {
                "current_0_30": round(grand_total_current, 2),
                "overdue_31_60": round(grand_total_30, 2),
                "overdue_61_90": round(grand_total_60, 2),
                "overdue_90_plus": round(grand_total_90, 2),
                "grand_total_receivables": round(grand_total_due, 2)
            },
            "customers": customer_aging
        }

    @staticmethod
    def get_customer_ledger(db: Session, business_id: int, customer_id: int) -> Dict[str, Any]:
        """Generate chronological Customer Statement of Account / Ledger with running balance."""
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.business_id == business_id
        ).first()

        if not customer:
            return {"error": "Customer not found"}

        invoices = db.query(Invoice).filter(
            Invoice.customer_id == customer_id,
            Invoice.status != "Cancelled"
        ).all()

        payments = db.query(Payment).filter(
            Payment.customer_id == customer_id
        ).all()

        # Combine into unified timeline
        entries = []
        for inv in invoices:
            entries.append({
                "date": inv.issue_date,
                "type": "INVOICE",
                "reference": inv.invoice_number,
                "description": f"Invoice: {inv.invoice_number} (Due: {inv.due_date})",
                "debit": inv.total_amount,   # Amount customer owes
                "credit": 0.0,
                "status": inv.status
            })

        for p in payments:
            entries.append({
                "date": p.payment_date,
                "type": "PAYMENT",
                "reference": p.payment_number,
                "description": f"Payment: {p.payment_number} via {p.payment_method} ({p.reference_number or 'No Ref'})",
                "debit": 0.0,
                "credit": p.amount,          # Amount customer paid
                "status": p.status
            })

        # Sort timeline by date ascending
        entries.sort(key=lambda x: (x["date"], 0 if x["type"] == "INVOICE" else 1))

        running_balance = 0.0
        statement = []
        for e in entries:
            running_balance += (e["debit"] - e["credit"])
            statement.append({
                "date": e["date"].isoformat(),
                "type": e["type"],
                "reference": e["reference"],
                "description": e["description"],
                "debit": round(e["debit"], 2),
                "credit": round(e["credit"], 2),
                "running_balance": round(running_balance, 2),
                "status": e["status"]
            })

        total_invoiced = sum(e["debit"] for e in entries)
        total_paid = sum(e["credit"] for e in entries)

        return {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "company_name": customer.company_name or customer.name,
                "phone": customer.phone,
                "city": customer.city,
                "ntn_number": customer.ntn_number,
                "credit_limit": customer.credit_limit,
                "current_balance": round(customer.current_balance, 2)
            },
            "summary": {
                "total_invoiced": round(total_invoiced, 2),
                "total_paid": round(total_paid, 2),
                "net_outstanding": round(customer.current_balance, 2)
            },
            "statement": statement
        }

    @staticmethod
    def get_reconciliation_summary(db: Session, business_id: int) -> Dict[str, Any]:
        """Summary of payment reconciliation status across the business."""
        invoices = db.query(Invoice).filter(Invoice.business_id == business_id).all()
        payments = db.query(Payment).filter(Payment.business_id == business_id).all()

        total_billed = sum(i.total_amount for i in invoices if i.status != "Cancelled")
        total_invoiced_paid = sum(i.paid_amount for i in invoices if i.status != "Cancelled")
        total_open_receivables = sum(i.balance_due for i in invoices if i.status not in ["Cancelled", "Paid"])

        total_payments_collected = sum(p.amount for p in payments)
        total_unallocated_cash = sum(p.unallocated_amount for p in payments)
        total_allocated_cash = round(total_payments_collected - total_unallocated_cash, 2)

        reconciliation_rate = 0.0
        if total_payments_collected > 0:
            reconciliation_rate = round((total_allocated_cash / total_payments_collected) * 100, 1)

        return {
            "total_billed": round(total_billed, 2),
            "total_open_receivables": round(total_open_receivables, 2),
            "total_payments_collected": round(total_payments_collected, 2),
            "total_allocated_cash": total_allocated_cash,
            "total_unallocated_cash": round(total_unallocated_cash, 2),
            "reconciliation_rate_percent": reconciliation_rate,
            "fully_reconciled_payments_count": len([p for p in payments if p.status == "Fully Reconciled"]),
            "unallocated_payments_count": len([p for p in payments if p.unallocated_amount > 0])
        }
