from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Dict, Any, List
from ..models import Invoice

class SimulatorService:

    @staticmethod
    def run_cash_flow_simulation(
        db: Session,
        business_id: int,
        collection_efficiency_pct: float = 80.0,
        average_delay_days: int = 15,
        default_risk_pct: float = 5.0,
        horizon_weeks: int = 6
    ) -> Dict[str, Any]:
        """
        Simulate future cash inflows from open accounts receivables under different distributor collection scenarios.
        """
        today = date.today()
        open_invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            Invoice.status.in_(["Issued", "Partially Paid", "Overdue"]),
            Invoice.balance_due > 0
        ).all()

        total_receivable = sum(inv.balance_due for inv in open_invoices)

        # Build weekly buckets
        weeks_labels = []
        baseline_inflow = [0.0] * horizon_weeks
        stress_inflow = [0.0] * horizon_weeks

        for w in range(horizon_weeks):
            start_w = today + timedelta(days=w * 7)
            end_w = start_w + timedelta(days=6)
            weeks_labels.append(f"Week {w+1} ({start_w.strftime('%d %b')})")

        # Distribute invoices across weeks based on due date
        for inv in open_invoices:
            # Baseline: expected on due date (if overdue, expected in week 1)
            days_from_now = (inv.due_date - today).days
            if days_from_now <= 0:
                base_week = 0
            else:
                base_week = min(horizon_weeks - 1, days_from_now // 7)

            baseline_inflow[base_week] += inv.balance_due

            # Scenario Simulation calculation:
            # Non-default portion
            recoverable_amount = inv.balance_due * (1.0 - (default_risk_pct / 100.0))
            on_time_portion = recoverable_amount * (collection_efficiency_pct / 100.0)
            delayed_portion = recoverable_amount * (1.0 - (collection_efficiency_pct / 100.0))

            # On-time lands in base_week
            stress_inflow[base_week] += on_time_portion

            # Delayed lands in base_week + (delay_days // 7)
            delayed_week = min(horizon_weeks - 1, base_week + max(1, average_delay_days // 7))
            stress_inflow[delayed_week] += delayed_portion

        # Round values
        baseline_inflow = [round(v, 2) for v in baseline_inflow]
        stress_inflow = [round(v, 2) for v in stress_inflow]

        total_baseline = sum(baseline_inflow)
        total_stress = sum(stress_inflow)
        expected_shortfall = round(max(0.0, total_baseline - total_stress), 2)
        potential_bad_debt = round(total_receivable * (default_risk_pct / 100.0), 2)

        # Dynamic advice based on results
        recommendations = []
        if default_risk_pct > 7:
            recommendations.append("High bad-debt risk detected. Mandate cash-on-delivery (COD) or bank pay-orders for orders exceeding Rs. 50,000.")
        if average_delay_days >= 20:
            recommendations.append("Average recovery delay is severe. Introduce early payment cash discounts (e.g., 2% if cleared within 7 days via Raast).")
        if total_receivable > 500000 and collection_efficiency_pct < 75:
            recommendations.append("Working capital crunch warning: Tighten credit terms from 30 days to 15 days for FMCG retailer accounts.")
        if not recommendations:
            recommendations.append("Healthy projected liquidity under current simulation parameters.")

        return {
            "parameters": {
                "collection_efficiency_pct": collection_efficiency_pct,
                "average_delay_days": average_delay_days,
                "default_risk_pct": default_risk_pct,
                "horizon_weeks": horizon_weeks
            },
            "metrics": {
                "total_open_receivables": round(total_receivable, 2),
                "simulated_recoverable_cash": round(total_stress, 2),
                "expected_liquidity_shortfall": expected_shortfall,
                "potential_bad_debt": potential_bad_debt
            },
            "chart_data": {
                "labels": weeks_labels,
                "baseline_expected": baseline_inflow,
                "simulated_scenario": stress_inflow
            },
            "recommendations": recommendations
        }
