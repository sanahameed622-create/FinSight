from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from ..models import Invoice, Payment, PaymentAllocation, Customer, ActivityLog

class ReconciliationService:

    @staticmethod
    def recalculate_customer_balance(db: Session, customer_id: int) -> float:
        """Calculate total net balance owed by customer: sum(invoice balance_due) - sum(payment unallocated_amount)."""
        invoices = db.query(Invoice).filter(
            Invoice.customer_id == customer_id,
            Invoice.status.notin_(["Cancelled", "Paid"])
        ).all()
        total_invoiced_due = sum(inv.balance_due for inv in invoices)

        payments = db.query(Payment).filter(
            Payment.customer_id == customer_id,
            Payment.unallocated_amount > 0
        ).all()
        total_unallocated_payments = sum(p.unallocated_amount for p in payments)

        net_balance = round(max(0.0, total_invoiced_due - total_unallocated_payments), 2)
        
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.current_balance = net_balance
            db.commit()
        return net_balance

    @classmethod
    def auto_reconcile_fifo(
        cls, 
        db: Session, 
        business_id: int, 
        customer_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        FIFO (First-In, First-Out) Smart Payment Reconciliation.
        Matches oldest unallocated payments against oldest outstanding invoices for a customer.
        """
        query_payments = db.query(Payment).filter(
            Payment.business_id == business_id,
            Payment.unallocated_amount > 0
        )
        if customer_id:
            query_payments = query_payments.filter(Payment.customer_id == customer_id)
        payments = query_payments.order_by(Payment.payment_date.asc(), Payment.id.asc()).all()

        total_allocated = 0.0
        allocations_count = 0
        affected_customers = set()

        for payment in payments:
            if payment.unallocated_amount <= 0:
                continue

            # Fetch open invoices for this specific customer in chronological order
            open_invoices = db.query(Invoice).filter(
                Invoice.business_id == business_id,
                Invoice.customer_id == payment.customer_id,
                Invoice.status.in_(["Issued", "Partially Paid", "Overdue"]),
                Invoice.balance_due > 0
            ).order_by(Invoice.issue_date.asc(), Invoice.id.asc()).all()

            for invoice in open_invoices:
                if payment.unallocated_amount <= 0:
                    break

                # Determine how much can be allocated
                allocatable = min(payment.unallocated_amount, invoice.balance_due)
                allocatable = round(allocatable, 2)

                if allocatable <= 0:
                    continue

                # Create allocation record
                allocation = PaymentAllocation(
                    payment_id=payment.id,
                    invoice_id=invoice.id,
                    allocated_amount=allocatable,
                    allocated_at=datetime.now(timezone.utc),
                    notes=f"Auto-FIFO matched with {payment.payment_number}"
                )
                db.add(allocation)

                # Update invoice
                invoice.paid_amount = round(invoice.paid_amount + allocatable, 2)
                invoice.balance_due = round(max(0.0, invoice.total_amount - invoice.paid_amount), 2)
                if invoice.balance_due <= 0.01:
                    invoice.status = "Paid"
                    invoice.balance_due = 0.0
                else:
                    invoice.status = "Partially Paid"

                # Update payment
                payment.unallocated_amount = round(payment.unallocated_amount - allocatable, 2)
                if payment.unallocated_amount <= 0.01:
                    payment.status = "Fully Reconciled"
                    payment.unallocated_amount = 0.0
                else:
                    payment.status = "Partially Allocated"

                total_allocated += allocatable
                allocations_count += 1
                affected_customers.add(payment.customer_id)

        # Recalculate customer balances
        for c_id in affected_customers:
            cls.recalculate_customer_balance(db, c_id)

        # Log activity
        if allocations_count > 0:
            log = ActivityLog(
                business_id=business_id,
                user_id=user_id,
                action_type="AUTO_RECONCILE",
                description=f"Auto-FIFO reconciled {allocations_count} invoice allocation(s) totaling PKR {total_allocated:,.2f}"
            )
            db.add(log)

        db.commit()

        # Compute remaining unallocated payments in business
        remaining_unallocated = db.query(Payment).filter(
            Payment.business_id == business_id,
            Payment.unallocated_amount > 0
        )
        if customer_id:
            remaining_unallocated = remaining_unallocated.filter(Payment.customer_id == customer_id)
        total_remaining = sum(p.unallocated_amount for p in remaining_unallocated.all())

        return {
            "success": True,
            "message": f"Successfully auto-reconciled {allocations_count} allocation(s).",
            "reconciled_allocations_count": allocations_count,
            "total_amount_allocated": round(total_allocated, 2),
            "unallocated_remaining": round(total_remaining, 2)
        }

    @classmethod
    def manual_reconcile(
        cls,
        db: Session,
        business_id: int,
        payment_id: int,
        allocations: List[Dict[str, Any]],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Manually allocate a payment to specific invoices."""
        payment = db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.business_id == business_id
        ).first()

        if not payment:
            return {"success": False, "message": "Payment not found"}

        requested_total = sum(item["amount_to_allocate"] for item in allocations)
        if requested_total > payment.unallocated_amount + 0.01:
            return {
                "success": False,
                "message": f"Requested allocation ({requested_total:,.2f}) exceeds available unallocated amount ({payment.unallocated_amount:,.2f})"
            }

        total_allocated = 0.0
        allocations_count = 0

        for item in allocations:
            invoice_id = item["invoice_id"]
            amount = round(item["amount_to_allocate"], 2)
            if amount <= 0:
                continue

            invoice = db.query(Invoice).filter(
                Invoice.id == invoice_id,
                Invoice.business_id == business_id
            ).first()

            if not invoice or invoice.status in ["Paid", "Cancelled"]:
                continue

            allocatable = min(amount, invoice.balance_due)
            allocatable = round(allocatable, 2)

            alloc = PaymentAllocation(
                payment_id=payment.id,
                invoice_id=invoice.id,
                allocated_amount=allocatable,
                allocated_at=datetime.now(timezone.utc),
                notes=f"Manual allocation from {payment.payment_number}"
            )
            db.add(alloc)

            invoice.paid_amount = round(invoice.paid_amount + allocatable, 2)
            invoice.balance_due = round(max(0.0, invoice.total_amount - invoice.paid_amount), 2)
            if invoice.balance_due <= 0.01:
                invoice.status = "Paid"
                invoice.balance_due = 0.0
            else:
                invoice.status = "Partially Paid"

            payment.unallocated_amount = round(payment.unallocated_amount - allocatable, 2)
            total_allocated += allocatable
            allocations_count += 1

        if payment.unallocated_amount <= 0.01:
            payment.status = "Fully Reconciled"
            payment.unallocated_amount = 0.0
        else:
            payment.status = "Partially Allocated"

        cls.recalculate_customer_balance(db, payment.customer_id)

        log = ActivityLog(
            business_id=business_id,
            user_id=user_id,
            action_type="MANUAL_RECONCILE",
            description=f"Manual allocation of PKR {total_allocated:,.2f} applied from payment {payment.payment_number}"
        )
        db.add(log)
        db.commit()

        return {
            "success": True,
            "message": f"Manual reconciliation complete. Allocated PKR {total_allocated:,.2f}",
            "reconciled_allocations_count": allocations_count,
            "total_amount_allocated": round(total_allocated, 2),
            "unallocated_remaining": round(payment.unallocated_amount, 2)
        }
