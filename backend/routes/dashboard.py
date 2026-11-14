from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Dict, Any
from ..database import get_db
from ..models import Invoice, Payment, Customer, ActivityLog, User
from ..dependencies import get_current_user
from ..services.report_service import ReportService
from ..services.ai_insights_service import AIInsightsService
from ..seeder import seed_sample_business_data

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    today = date.today()
    first_of_month = today.replace(day=1)
    business_id = current_user.business_id

    # Open Receivables
    open_invoices = db.query(Invoice).filter(
        Invoice.business_id == business_id,
        Invoice.status.in_(["Issued", "Partially Paid", "Overdue"])
    ).all()
    total_receivables = sum(inv.balance_due for inv in open_invoices)

    # Overdue Receivables
    overdue_receivables = sum(inv.balance_due for inv in open_invoices if inv.due_date < today)

    # Monthly Collections
    month_payments = db.query(Payment).filter(
        Payment.business_id == business_id,
        Payment.payment_date >= first_of_month
    ).all()
    collections_this_month = sum(p.amount for p in month_payments)

    # Unallocated Cash
    unallocated_payments = db.query(Payment).filter(
        Payment.business_id == business_id,
        Payment.unallocated_amount > 0
    ).all()
    total_unallocated_cash = sum(p.unallocated_amount for p in unallocated_payments)

    # Active Customers Count
    active_customers_count = db.query(Customer).filter(
        Customer.business_id == business_id,
        Customer.is_active == True
    ).count()

    # Aging Buckets
    aging_data = ReportService.get_aging_report(db, business_id)["summary"]

    # Recent Activity
    activities = db.query(ActivityLog).filter(
        ActivityLog.business_id == business_id
    ).order_by(ActivityLog.created_at.desc()).limit(8).all()

    recent_logs = [
        {
            "id": a.id,
            "action_type": a.action_type,
            "description": a.description,
            "time": a.created_at.strftime("%d %b, %I:%M %p")
        }
        for a in activities
    ]

    # Cash Flow Trend (Last 6 Months)
    trend_labels = []
    invoiced_trend = []
    collected_trend = []

    for i in range(5, -1, -1):
        # Calculate month offsets safely
        m_year = today.year
        m_month = today.month - i
        while m_month <= 0:
            m_month += 12
            m_year -= 1
        
        start_dt = date(m_year, m_month, 1)
        if m_month == 12:
            end_dt = date(m_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_dt = date(m_year, m_month + 1, 1) - timedelta(days=1)

        month_label = start_dt.strftime("%b %y")
        trend_labels.append(month_label)

        # Invoiced in this month
        inv_sum = sum(
            inv.total_amount for inv in db.query(Invoice).filter(
                Invoice.business_id == business_id,
                Invoice.issue_date >= start_dt,
                Invoice.issue_date <= end_dt,
                Invoice.status != "Cancelled"
            ).all()
        )
        invoiced_trend.append(round(inv_sum, 2))

        # Collected in this month
        pay_sum = sum(
            p.amount for p in db.query(Payment).filter(
                Payment.business_id == business_id,
                Payment.payment_date >= start_dt,
                Payment.payment_date <= end_dt
            ).all()
        )
        collected_trend.append(round(pay_sum, 2))

    # AI Insights
    ai_data = AIInsightsService.generate_insights(db, business_id)

    return {
        "kpis": {
            "total_receivables": round(total_receivables, 2),
            "collections_this_month": round(collections_this_month, 2),
            "overdue_receivables": round(overdue_receivables, 2),
            "unallocated_cash": round(total_unallocated_cash, 2),
            "active_customers_count": active_customers_count
        },
        "aging_distribution": aging_data,
        "cash_flow_trend": {
            "labels": trend_labels,
            "invoiced": invoiced_trend,
            "collected": collected_trend
        },
        "ai_insights": ai_data,
        "recent_activities": recent_logs
    }

@router.post("/load-sample-data")
def load_sample_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cust_count = db.query(Customer).filter(Customer.business_id == current_user.business_id).count()
    if cust_count > 0:
        return {
            "success": False,
            "message": "Sample data is already present in your workspace."
        }
    seed_sample_business_data(db, current_user.business_id, current_user.id)
    return {
        "success": True,
        "message": "Sample Pakistani B2B FMCG data (customers, products, invoices, and cheques) loaded successfully!"
    }
