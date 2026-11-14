from datetime import date, timedelta
from sqlalchemy.orm import Session
from .models import Base, User, Business, Customer, Invoice, InvoiceItem, Payment, PaymentAllocation, ActivityLog, Product, PostDatedCheque
from .utils.security import get_password_hash
from .services.reconciliation_service import ReconciliationService

def seed_demo_data(db: Session):
    """Seed realistic initial data for Pakistani B2B FMCG Wholesalers."""
    # Check if data already exists
    existing_biz = db.query(Business).first()
    if existing_biz:
        # Seed missing products or cheques if needed
        if not db.query(Product).filter(Product.business_id == existing_biz.id).first():
            products = [
                Product(business_id=existing_biz.id, sku="FMCG-DAL-5L", name="Dalda Cooking Oil 5L (Carton of 4)", category="Edible Oils", unit="Carton", stock_quantity=150.0, unit_cost=5800.0, unit_price=6500.0, reorder_level=20.0),
                Product(business_id=existing_biz.id, sku="FMCG-TAP-450G", name="Tapal Danedar Tea 450g (Carton of 24)", category="Beverages", unit="Carton", stock_quantity=85.0, unit_cost=4800.0, unit_price=5500.0, reorder_level=15.0),
                Product(business_id=existing_biz.id, sku="FMCG-SHN-MAS", name="Shan Biryani Masala (Carton of 48)", category="Spices & Seasoning", unit="Carton", stock_quantity=120.0, unit_cost=3400.0, unit_price=4000.0, reorder_level=25.0),
                Product(business_id=existing_biz.id, sku="FMCG-GRD-10KG", name="Guard Supreme Basmati Rice 10kg", category="Grains & Staples", unit="Bag", stock_quantity=200.0, unit_cost=2500.0, unit_price=3000.0, reorder_level=30.0),
                Product(business_id=existing_biz.id, sku="FMCG-NAT-KCH", name="National Foods Ketchup 1kg (Carton of 12)", category="Condiments", unit="Carton", stock_quantity=60.0, unit_cost=3600.0, unit_price=4200.0, reorder_level=10.0),
            ]
            db.add_all(products)
            db.commit()
        cust = db.query(Customer).filter(Customer.business_id == existing_biz.id).first()
        if cust and not db.query(PostDatedCheque).filter(PostDatedCheque.business_id == existing_biz.id).first():
            today = date.today()
            chq = PostDatedCheque(
                business_id=existing_biz.id,
                customer_id=cust.id,
                cheque_number="ABL-4019284",
                bank_name="Allied Bank Limited (ABL)",
                amount=85000.0,
                issue_date=today - timedelta(days=2),
                maturity_date=today + timedelta(days=7),
                status="Pending Deposit",
                notes="Post-dated cheque for upcoming FMCG shipment"
            )
            db.add(chq)
            db.commit()
        return

    # 1. Create Business
    biz = Business(
        name="Al-Rehman FMCG Wholesalers",
        registration_no="NTN-4829104-7",
        phone="+92 42 37651234",
        city="Lahore",
        address="Shop # 14-B, Circular Road Wholesale Market, Lahore",
        currency="PKR"
    )
    db.add(biz)
    db.flush()

    # 2. Create Admin User
    admin = User(
        business_id=biz.id,
        full_name="Muhammad Usman",
        email="admin@finsight.pk",
        phone="+92 300 8472910",
        hashed_password=get_password_hash("admin123"),
        role="admin"
    )
    db.add(admin)
    db.flush()

    # 3. Create Key B2B Customers
    c1 = Customer(
        business_id=biz.id,
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
        business_id=biz.id,
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
        business_id=biz.id,
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
        business_id=biz.id,
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
        business_id=biz.id,
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

    # 4. Invoices
    # Invoice 1: Lahore Super Mart - Overdue 40 days
    inv1 = Invoice(
        business_id=biz.id,
        customer_id=c1.id,
        invoice_number="INV-2026-0001",
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
    # Invoice 2: Lahore Super Mart - Current (Due in 5 days)
    inv2 = Invoice(
        business_id=biz.id,
        customer_id=c1.id,
        invoice_number="INV-2026-0002",
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
    # Invoice 3: Madina Cash & Carry - Due in 12 days
    inv3 = Invoice(
        business_id=biz.id,
        customer_id=c2.id,
        invoice_number="INV-2026-0003",
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
    # Invoice 4: Karachi B2B Grocers - Overdue 70 days (High Risk)
    inv4 = Invoice(
        business_id=biz.id,
        customer_id=c3.id,
        invoice_number="INV-2026-0004",
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
    # Invoice 5: Faisalabad Traders - Due in 20 days
    inv5 = Invoice(
        business_id=biz.id,
        customer_id=c5.id,
        invoice_number="INV-2026-0005",
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

    # Add line items
    item1 = InvoiceItem(invoice_id=inv1.id, item_description="Dalda Cooking Oil 5L (Carton of 4)", quantity=20.0, unit_price=6500.0, total=130000.0)
    item2 = InvoiceItem(invoice_id=inv1.id, item_description="Tapal Danedar Tea 450g (Carton of 24)", quantity=10.0, unit_price=5500.0, total=55000.0)
    item3 = InvoiceItem(invoice_id=inv2.id, item_description="Shan Biryani Masala (Carton of 48)", quantity=20.0, unit_price=4000.0, total=80000.0)
    item4 = InvoiceItem(invoice_id=inv2.id, item_description="Guard Supreme Basmati Rice 10kg", quantity=20.0, unit_price=3000.0, total=60000.0)
    db.add_all([item1, item2, item3, item4])
    db.flush()

    # 5. Payments
    # Payment 1: Lahore Super Mart paid 120,000 via Raast (unallocated, ready for FIFO match)
    p1 = Payment(
        business_id=biz.id,
        customer_id=c1.id,
        payment_number="PAY-2026-0001",
        payment_date=today - timedelta(days=2),
        amount=120000.0,
        unallocated_amount=120000.0,
        payment_method="Raast",
        reference_number="RAAST-98237190",
        bank_name="Meezan Bank Raast",
        status="Unallocated",
        notes="Online payment received via Raast ID"
    )
    # Payment 2: Madina Cash & Carry paid 100,000 via Cheque (Bank Transfer)
    p2 = Payment(
        business_id=biz.id,
        customer_id=c2.id,
        payment_number="PAY-2026-0002",
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

    # 6. Seed Inventory Products if none exist
    if not db.query(Product).filter(Product.business_id == biz.id).first():
        products = [
            Product(business_id=biz.id, sku="FMCG-DAL-5L", name="Dalda Cooking Oil 5L (Carton of 4)", category="Edible Oils", unit="Carton", stock_quantity=150.0, unit_cost=5800.0, unit_price=6500.0, reorder_level=20.0),
            Product(business_id=biz.id, sku="FMCG-TAP-450G", name="Tapal Danedar Tea 450g (Carton of 24)", category="Beverages", unit="Carton", stock_quantity=85.0, unit_cost=4800.0, unit_price=5500.0, reorder_level=15.0),
            Product(business_id=biz.id, sku="FMCG-SHN-MAS", name="Shan Biryani Masala (Carton of 48)", category="Spices & Seasoning", unit="Carton", stock_quantity=120.0, unit_cost=3400.0, unit_price=4000.0, reorder_level=25.0),
            Product(business_id=biz.id, sku="FMCG-GRD-10KG", name="Guard Supreme Basmati Rice 10kg", category="Grains & Staples", unit="Bag", stock_quantity=200.0, unit_cost=2500.0, unit_price=3000.0, reorder_level=30.0),
            Product(business_id=biz.id, sku="FMCG-NAT-KCH", name="National Foods Ketchup 1kg (Carton of 12)", category="Condiments", unit="Carton", stock_quantity=60.0, unit_cost=3600.0, unit_price=4200.0, reorder_level=10.0),
        ]
        db.add_all(products)
        db.flush()

    # 7. Seed Post-Dated Cheques (PDC) if none exist
    if not db.query(PostDatedCheque).filter(PostDatedCheque.business_id == biz.id).first():
        chq1 = PostDatedCheque(
            business_id=biz.id,
            customer_id=c2.id,
            cheque_number="ABL-4019284",
            bank_name="Allied Bank Limited (ABL)",
            amount=85000.0,
            issue_date=today - timedelta(days=2),
            maturity_date=today + timedelta(days=7),
            status="Pending Deposit",
            notes="Post-dated cheque for upcoming FMCG shipment"
        )
        chq2 = PostDatedCheque(
            business_id=biz.id,
            customer_id=c4.id,
            cheque_number="MCB-9182741",
            bank_name="MCB Bank",
            amount=150000.0,
            issue_date=today - timedelta(days=1),
            maturity_date=today + timedelta(days=14),
            status="Pending Deposit",
            notes="Post-dated security cheque"
        )
        db.add_all([chq1, chq2])
        db.flush()

    # 8. Recalculate balances
    for cust in [c1, c2, c3, c4, c5]:
        ReconciliationService.recalculate_customer_balance(db, cust.id)

    # 9. Initial Activity Log
    log = ActivityLog(
        business_id=biz.id,
        user_id=admin.id,
        action_type="SYSTEM_INITIALIZE",
        description="Demo B2B Wholesale workspace initialized with sample FMCG customers, invoices and unallocated payments."
    )
    db.add(log)
    db.commit()
    print("Database successfully seeded with demo FMCG B2B data!")
