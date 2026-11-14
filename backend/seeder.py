import os
from datetime import date, timedelta
from sqlalchemy.orm import Session
from .models import Base, User, Business, Customer, Invoice, InvoiceItem, Payment, PaymentAllocation, ActivityLog, Product, PostDatedCheque
from .utils.security import get_password_hash
from .services.reconciliation_service import ReconciliationService

def seed_sample_business_data(db: Session, business_id: int, user_id: int = None):
    """
    Populates realistic Pakistani B2B FMCG data (customers, products, invoices, payments, cheques)
    for a given authenticated business tenant. Never creates users or passwords.
    """
    # 1. Check if business already has customers
    existing_cust = db.query(Customer).filter(Customer.business_id == business_id).first()
    if existing_cust:
        return

    # 2. Key B2B Customers
    c1 = Customer(
        business_id=business_id,
        name="Lahore Super Mart",
        company_name="Lahore Super Mart Pvt Ltd",
        phone="0300-4567891",
        email="accounts@lahoresupermart.pk",
        city="Lahore",
        address="Plot 42, Main Boulevard, Gulberg III, Lahore",
        ntn_number="3029182-1",
        credit_limit=600000.0,
        payment_terms_days=15
    )
    c2 = Customer(
        business_id=business_id,
        name="Madina Cash & Carry",
        company_name="Madina Retailers Network",
        phone="0321-9876543",
        email="madinacash@gmail.com",
        city="Lahore",
        address="Peco Road, Faisal Town, Lahore",
        ntn_number="7821903-4",
        credit_limit=450000.0,
        payment_terms_days=15
    )
    c3 = Customer(
        business_id=business_id,
        name="Karachi B2B Grocers",
        company_name="Karachi B2B Supply Corp",
        phone="0333-1122334",
        email="info@karachib2b.com",
        city="Karachi",
        address="Daryalal Street, Jodia Bazaar, Karachi",
        ntn_number="1928475-6",
        credit_limit=1200000.0,
        payment_terms_days=30
    )
    c4 = Customer(
        business_id=business_id,
        name="Rawalpindi Wholesale Hub",
        company_name="Raja Bazaar Distribution Co",
        phone="0345-5566778",
        email="accounts@rajabazaar.pk",
        city="Rawalpindi",
        address="Grain Market, Raja Bazaar, Rawalpindi",
        ntn_number="9028174-2",
        credit_limit=500000.0,
        payment_terms_days=20
    )
    c5 = Customer(
        business_id=business_id,
        name="Faisalabad Grain & Oil Traders",
        company_name="Chaudhry & Sons Wholesalers",
        phone="0312-3344556",
        email="chaudhry.grain@gmail.com",
        city="Faisalabad",
        address="Circular Road, Gol Karyana, Faisalabad",
        ntn_number="5849102-3",
        credit_limit=800000.0,
        payment_terms_days=25
    )
    db.add_all([c1, c2, c3, c4, c5])
    db.flush()

    today = date.today()

    # 3. Invoices
    inv1 = Invoice(
        business_id=business_id,
        customer_id=c1.id,
        invoice_number=f"INV-{business_id}-0001",
        issue_date=today - timedelta(days=55),
        due_date=today - timedelta(days=40),
        subtotal=185000.0,
        tax_amount=0.0,
        discount_amount=0.0,
        total_amount=185000.0,
        paid_amount=0.0,
        balance_due=185000.0,
        status="Overdue",
        notes="Dalda Cooking Oil 5L (20 Ctns) & Tapal Tea 450g (15 Ctns)"
    )
    inv2 = Invoice(
        business_id=business_id,
        customer_id=c1.id,
        invoice_number=f"INV-{business_id}-0002",
        issue_date=today - timedelta(days=10),
        due_date=today + timedelta(days=5),
        subtotal=140000.0,
        tax_amount=0.0,
        discount_amount=0.0,
        total_amount=140000.0,
        paid_amount=0.0,
        balance_due=140000.0,
        status="Issued",
        notes="Shan Biryani Masala (25 Ctns) & Guard Basmati Rice 10kg (40 Bags)"
    )
    inv3 = Invoice(
        business_id=business_id,
        customer_id=c2.id,
        invoice_number=f"INV-{business_id}-0003",
        issue_date=today - timedelta(days=3),
        due_date=today + timedelta(days=12),
        subtotal=220000.0,
        tax_amount=0.0,
        discount_amount=0.0,
        total_amount=220000.0,
        paid_amount=0.0,
        balance_due=220000.0,
        status="Issued",
        notes="National Foods Tomato Ketchup 1kg (30 Ctns) & Mitchell's Jam (20 Ctns)"
    )
    inv4 = Invoice(
        business_id=business_id,
        customer_id=c3.id,
        invoice_number=f"INV-{business_id}-0004",
        issue_date=today - timedelta(days=100),
        due_date=today - timedelta(days=70),
        subtotal=450000.0,
        tax_amount=0.0,
        discount_amount=0.0,
        total_amount=450000.0,
        paid_amount=0.0,
        balance_due=450000.0,
        status="Overdue",
        notes="Bulk FMCG Consignment dispatched via Karachi Goods Transport"
    )
    inv5 = Invoice(
        business_id=business_id,
        customer_id=c5.id,
        invoice_number=f"INV-{business_id}-0005",
        issue_date=today - timedelta(days=5),
        due_date=today + timedelta(days=20),
        subtotal=310000.0,
        tax_amount=0.0,
        discount_amount=0.0,
        total_amount=310000.0,
        paid_amount=0.0,
        balance_due=310000.0,
        status="Issued",
        notes="Habib Cooking Oil 16L Tins (50 units)"
    )
    db.add_all([inv1, inv2, inv3, inv4, inv5])
    db.flush()

    # Line items
    item1 = InvoiceItem(invoice_id=inv1.id, item_description="Dalda Cooking Oil 5L (Carton of 4)", quantity=20.0, unit_price=6500.0, total=130000.0)
    item2 = InvoiceItem(invoice_id=inv1.id, item_description="Tapal Danedar Tea 450g (Carton of 24)", quantity=10.0, unit_price=5500.0, total=55000.0)
    item3 = InvoiceItem(invoice_id=inv2.id, item_description="Shan Biryani Masala (Carton of 48)", quantity=20.0, unit_price=4000.0, total=80000.0)
    item4 = InvoiceItem(invoice_id=inv2.id, item_description="Guard Supreme Basmati Rice 10kg", quantity=20.0, unit_price=3000.0, total=60000.0)
    db.add_all([item1, item2, item3, item4])
    db.flush()

    # 4. Payments
    p1 = Payment(
        business_id=business_id,
        customer_id=c1.id,
        payment_number=f"PAY-{business_id}-0001",
        payment_date=today - timedelta(days=2),
        amount=120000.0,
        unallocated_amount=120000.0,
        payment_method="Raast",
        reference_number="RAAST-98237190",
        bank_name="Meezan Bank Raast",
        status="Unallocated",
        notes="Online payment received via Raast ID"
    )
    p2 = Payment(
        business_id=business_id,
        customer_id=c2.id,
        payment_number=f"PAY-{business_id}-0002",
        payment_date=today - timedelta(days=1),
        amount=100000.0,
        unallocated_amount=100000.0,
        payment_method="Bank Transfer",
        reference_number="HBL-FT-4910284",
        bank_name="Habib Bank Limited (HBL)",
        status="Unallocated",
        notes="Advance partial payment for weekly delivery"
    )
    db.add_all([p1, p2])
    db.flush()

    # 5. Inventory Products
    products = [
        Product(business_id=business_id, sku="FMCG-DAL-5L", name="Dalda Cooking Oil 5L (Carton of 4)", category="Edible Oils", unit="Carton", stock_quantity=150.0, unit_cost=5800.0, unit_price=6500.0, reorder_level=20.0),
        Product(business_id=business_id, sku="FMCG-TAP-450G", name="Tapal Danedar Tea 450g (Carton of 24)", category="Beverages", unit="Carton", stock_quantity=85.0, unit_cost=4800.0, unit_price=5500.0, reorder_level=15.0),
        Product(business_id=business_id, sku="FMCG-SHN-MAS", name="Shan Biryani Masala (Carton of 48)", category="Spices & Seasoning", unit="Carton", stock_quantity=120.0, unit_cost=3400.0, unit_price=4000.0, reorder_level=25.0),
        Product(business_id=business_id, sku="FMCG-GRD-10KG", name="Guard Supreme Basmati Rice 10kg", category="Grains & Staples", unit="Bag", stock_quantity=200.0, unit_cost=2500.0, unit_price=3000.0, reorder_level=30.0),
        Product(business_id=business_id, sku="FMCG-NAT-KCH", name="National Foods Ketchup 1kg (Carton of 12)", category="Condiments", unit="Carton", stock_quantity=60.0, unit_cost=3600.0, unit_price=4200.0, reorder_level=10.0),
    ]
    db.add_all(products)
    db.flush()

    # 6. Post-Dated Cheques (PDC)
    chq1 = PostDatedCheque(
        business_id=business_id,
        customer_id=c2.id,
        cheque_number=f"ABL-{business_id}-4019284",
        bank_name="Allied Bank Limited (ABL)",
        amount=85000.0,
        issue_date=today - timedelta(days=2),
        maturity_date=today + timedelta(days=7),
        status="Pending Deposit",
        notes="Post-dated cheque for upcoming FMCG shipment"
    )
    chq2 = PostDatedCheque(
        business_id=business_id,
        customer_id=c4.id,
        cheque_number=f"MCB-{business_id}-9182741",
        bank_name="MCB Bank",
        amount=150000.0,
        issue_date=today - timedelta(days=1),
        maturity_date=today + timedelta(days=14),
        status="Pending Deposit",
        notes="Post-dated security cheque"
    )
    db.add_all([chq1, chq2])
    db.flush()

    # 7. Recalculate balances
    for cust in [c1, c2, c3, c4, c5]:
        ReconciliationService.recalculate_customer_balance(db, cust.id)

    # 8. Activity Log
    if user_id:
        log = ActivityLog(
            business_id=business_id,
            user_id=user_id,
            action_type="SYSTEM_INITIALIZE",
            description="Initial wholesale catalog and customer accounts loaded."
        )
        db.add(log)
    db.commit()


def seed_demo_data(db: Session):
    """
    Optional initialization function.
    In production, this strictly requires DEMO_ADMIN_EMAIL and DEMO_ADMIN_PASSWORD
    to be set in the environment. Hardcoded passwords are never used.
    """
    admin_email = os.getenv("DEMO_ADMIN_EMAIL")
    admin_password = os.getenv("DEMO_ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        # Standard production behavior: do not create any backdoor user accounts
        return

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == admin_email).first()
    if existing_user:
        return

    biz = Business(
        name=os.getenv("DEMO_BUSINESS_NAME", "Wholesale Distribution Hub"),
        registration_no="NTN-4829104-7",
        phone="+92 42 37651234",
        city="Lahore",
        address="Wholesale Market, Lahore",
        currency="PKR"
    )
    db.add(biz)
    db.flush()

    admin = User(
        business_id=biz.id,
        full_name=os.getenv("DEMO_ADMIN_NAME", "Platform Administrator"),
        email=admin_email,
        phone="+92 300 0000000",
        hashed_password=get_password_hash(admin_password),
        role="admin"
    )
    db.add(admin)
    db.flush()

    seed_sample_business_data(db, biz.id, admin.id)
    print(f"[SECURE SEEDER] Demo business created for {admin_email} from environment configuration.")
