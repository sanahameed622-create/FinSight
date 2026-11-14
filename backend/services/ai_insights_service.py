from sqlalchemy.orm import Session
from datetime import date
from typing import Dict, Any, List
from ..models import Invoice, Payment, Customer

class AIInsightsService:

    @staticmethod
    def generate_insights(db: Session, business_id: int) -> Dict[str, Any]:
        """
        Produce AI-driven financial intelligence, risk warnings, and actionable recommendations.
        """
        today = date.today()
        customers = db.query(Customer).filter(Customer.business_id == business_id).all()
        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            Invoice.status != "Cancelled"
        ).all()
        payments = db.query(Payment).filter(Payment.business_id == business_id).all()

        total_receivable = sum(c.current_balance for c in customers)
        unallocated_cash = sum(p.unallocated_amount for p in payments)

        insights_list: List[Dict[str, Any]] = []

        # 1. Unallocated Cash Reconciliation Alert
        if unallocated_cash > 0:
            insights_list.append({
                "type": "opportunity",
                "severity": "medium",
                "title": "Unallocated Cash Ready for Matching",
                "message": f"PKR {unallocated_cash:,.2f} in received payments is currently sitting unallocated. Running Smart FIFO auto-reconciliation will instantly clear customer ledgers.",
                "action": "AUTO_RECONCILE",
                "metric": f"PKR {unallocated_cash:,.2f}"
            })

        # 2. Debtor Concentration Risk
        if customers and total_receivable > 0:
            sorted_custs = sorted(customers, key=lambda c: c.current_balance, reverse=True)
            top_3 = sorted_custs[:3]
            top_3_balance = sum(c.current_balance for c in top_3)
            concentration_pct = round((top_3_balance / total_receivable) * 100, 1)

            if concentration_pct >= 60:
                top_names = ", ".join(c.name for c in top_3 if c.current_balance > 0)
                insights_list.append({
                    "type": "risk",
                    "severity": "high",
                    "title": f"High Receivables Concentration ({concentration_pct}%)",
                    "message": f"Top 3 debtors ({top_names}) account for {concentration_pct}% of total outstanding credit. A payment delay from these key accounts will severely affect wholesale inventory restocking.",
                    "action": "CREDIT_REVIEW",
                    "metric": f"{concentration_pct}%"
                })

        # 3. Severe Overdue Detection (Aging > 60 days)
        severe_overdue_invoices = [
            inv for inv in invoices 
            if inv.status in ["Issued", "Partially Paid", "Overdue"] 
            and (today - inv.due_date).days > 60
            and inv.balance_due > 0
        ]
        if severe_overdue_invoices:
            severe_total = sum(i.balance_due for i in severe_overdue_invoices)
            insights_list.append({
                "type": "danger",
                "severity": "high",
                "title": f"Critical Overdue Debt (60+ Days)",
                "message": f"PKR {severe_total:,.2f} across {len(severe_overdue_invoices)} invoice(s) is overdue by more than 60 days. Immediate collection recovery or delivery freeze is advised.",
                "action": "SEND_REMINDERS",
                "metric": f"PKR {severe_total:,.2f}"
            })

        # 4. Credit Limit Breach Analysis
        over_limit_customers = [c for c in customers if c.current_balance > c.credit_limit and c.credit_limit > 0]
        if over_limit_customers:
            names = ", ".join(c.name for c in over_limit_customers[:2])
            insights_list.append({
                "type": "warning",
                "severity": "medium",
                "title": "Credit Limit Exceeded",
                "message": f"{len(over_limit_customers)} customer(s) ({names}) have exceeded their approved credit limit. Put new order dispatches on hold until ledger balance is paid.",
                "action": "LOCK_CREDIT",
                "metric": f"{len(over_limit_customers)} Accounts"
            })

        # 5. Positive Health Indicator if none of the above are critical
        if not insights_list:
            insights_list.append({
                "type": "positive",
                "severity": "low",
                "title": "Healthy Financial Flow",
                "message": "All invoices are within standard payment terms and payment allocations are up to date.",
                "action": "MONITOR",
                "metric": "100% On-Track"
            })

        # Summary Financial Health Score (0 - 100)
        health_score = 100
        if total_receivable > 0:
            overdue_sum = sum(
                inv.balance_due for inv in invoices 
                if inv.status in ["Issued", "Partially Paid", "Overdue"] 
                and inv.due_date < today
            )
            overdue_ratio = overdue_sum / total_receivable
            health_score -= int(overdue_ratio * 40)

        if unallocated_cash > 0:
            health_score -= 10

        health_score = max(20, min(100, health_score))

        return {
            "health_score": health_score,
            "status": "Excellent" if health_score >= 85 else ("Good" if health_score >= 70 else "At Risk"),
            "insights": insights_list
        }
