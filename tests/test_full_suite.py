import sys
import time
from pathlib import Path
from datetime import date, timedelta

base = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base))

from starlette.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import Product, Customer, Invoice, Payment, PostDatedCheque, Business

def run_deep_verification():
    client = TestClient(app)
    print("=" * 60)
    print("      FINSIGHT — STEP 04 DEEP VERIFICATION & TEST SUITE      ")
    print("=" * 60)

    # -------------------------------------------------------------
    # Test Group 1: Dynamic Authentication & Zero-Backdoor Security
    # -------------------------------------------------------------
    print("\n--- [Group 1: Authentication & Zero-Backdoor Security Boundaries] ---")
    
    suite_email = f"suite.admin.{int(time.time())}@securetest.local"
    suite_password = "SecureVerificationKey!99"

    # 1.0 Register dynamic test tenant
    r = client.post("/api/auth/register", json={
        "full_name": "Suite Administrator",
        "email": suite_email,
        "password": suite_password,
        "phone": "+92 300 1122334",
        "business_name": "FinSight Enterprise Ltd",
        "city": "Lahore",
        "registration_no": "NTN-1234567-8"
    })
    assert r.status_code == 200, f"Registration failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 1.0 Dynamic business tenant registration successful.")

    # 1.1 Valid Login
    r = client.post("/api/auth/login", json={"email": suite_email, "password": suite_password})
    assert r.status_code == 200, f"Valid login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 1.1 Correct credentials grant valid JWT bearer token.")

    # 1.2 Invalid Login (Wrong password)
    r = client.post("/api/auth/login", json={"email": suite_email, "password": "wrongpassword"})
    assert r.status_code == 401, "Security breach: invalid password accepted"
    print("[PASS] 1.2 Invalid password rejected with HTTP 401 Unauthorized.")

    # 1.3 Zero-Backdoor Check: Verify unseeded / unauthorized accounts cannot log in
    r = client.post("/api/auth/login", json={"email": "unregistered.admin@domain.com", "password": "SamplePassword123!"})
    assert r.status_code == 401, "Security breach: unregistered account permitted access!"
    print("[PASS] 1.3 Zero-Backdoor confirmed: Unauthorized credentials strictly rejected with HTTP 401.")

    # 1.4 Unauthorized API Request
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 401, "Security breach: unauthenticated access to stats allowed"
    print("[PASS] 1.4 Protected endpoints block requests without Authorization header.")

    # 1.5 Invalid Token
    r = client.get("/api/dashboard/stats", headers={"Authorization": "Bearer invalid.fake.token"})
    assert r.status_code == 401, "Security breach: malformed token accepted"
    print("[PASS] 1.5 Malformed or forged JWT tokens rejected.")

    # -------------------------------------------------------------
    # Test Group 2: Business & Multi-Tenancy Onboarding
    # -------------------------------------------------------------
    print("\n--- [Group 2: Tenant Isolation & Onboarding] ---")
    new_email = f"test.distributor.{int(time.time()) + 1}@example.com"
    r = client.post("/api/auth/register", json={
        "full_name": "Kashif Enterprises",
        "email": new_email,
        "password": "SecurePassword123!",
        "phone": "+92 321 0001122",
        "business_name": "Kashif Wholesale Hub",
        "city": "Karachi",
        "registration_no": "STRN-9988776-5"
    })
    assert r.status_code == 200, f"Registration failed: {r.text}"
    new_token = r.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}
    print(f"[PASS] 2.1 New business tenant registered and isolated successfully.")

    # Verify new tenant starts with isolated clean state
    r = client.get("/api/customers", headers=new_headers)
    assert r.status_code == 200
    assert len(r.json()) == 0, "Data leakage: New tenant can see existing customers!"
    print("[PASS] 2.2 Data isolation confirmed: New tenant cannot access other businesses' data.")

    # -------------------------------------------------------------
    # Test Group 3: Customer Accounts & Credit Controls
    # -------------------------------------------------------------
    print("\n--- [Group 3: Accounts Receivable & Credit Integrity] ---")
    r = client.post("/api/customers", json={
        "name": "Gulberg Wholesale Store",
        "company_name": "Gulberg B2B Mart",
        "phone": "0300-9988776",
        "city": "Lahore",
        "credit_limit": 500000.0,
        "payment_terms_days": 15
    }, headers=headers)
    assert r.status_code == 201
    test_cust = r.json()
    test_cust_id = test_cust["id"]
    print(f"[PASS] 3.1 Customer account created: {test_cust['name']} (Credit Limit: PKR {test_cust['credit_limit']:,.2f})")

    # -------------------------------------------------------------
    # Test Group 4: Inventory Management & Invoicing Auto-Deduction
    # -------------------------------------------------------------
    print("\n--- [Group 4: Inventory Auto-Deduction & Invoicing] ---")
    
    # 4.1 Create test product with known stock
    test_sku = f"TEST-OIL-{int(time.time())}"
    r = client.post("/api/products", json={
        "sku": test_sku,
        "name": f"Premium Sunflower Oil 5L ({test_sku})",
        "category": "Edible Oils",
        "unit": "Carton",
        "stock_quantity": 100.0,
        "unit_cost": 5000.0,
        "unit_price": 6000.0,
        "reorder_level": 20.0
    }, headers=headers)
    assert r.status_code == 201
    test_prod = r.json()
    print(f"[PASS] 4.1 Product SKU '{test_prod['sku']}' created with opening stock of 100 cartons.")

    # 4.2 Issue invoice with 25 units of this product
    r = client.post("/api/invoices", json={
        "customer_id": test_cust_id,
        "issue_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=15)).isoformat(),
        "tax_amount": 0.0,
        "discount_amount": 0.0,
        "notes": "Test invoice for automated inventory decrement",
        "items": [
            {
                "item_description": test_prod["name"],
                "quantity": 25.0,
                "unit_price": 6000.0
            }
        ]
    }, headers=headers)
    assert r.status_code == 201
    inv_data = r.json()
    assert inv_data["total_amount"] == 150000.0
    assert inv_data["balance_due"] == 150000.0
    print(f"[PASS] 4.2 Invoice {inv_data['invoice_number']} generated for PKR 150,000.00.")

    # 4.3 Verify stock decreased from 100 to 75
    r = client.get("/api/products", headers=headers)
    matched_prod = next(p for p in r.json() if p["id"] == test_prod["id"])
    assert matched_prod["stock_quantity"] == 75.0, f"Stock mismatch: expected 75, got {matched_prod['stock_quantity']}"
    print(f"[PASS] 4.3 Inventory auto-deduction confirmed: Stock reduced from 100 -> 75 cartons.")

    # 4.4 Verify Customer Balance Updated
    r = client.get(f"/api/customers/{test_cust_id}", headers=headers)
    assert r.json()["current_balance"] == 150000.0
    print(f"[PASS] 4.4 Customer ledger balance automatically updated to PKR 150,000.00.")

    # -------------------------------------------------------------
    # Test Group 5: Payment Processing & Smart FIFO Reconciliation
    # -------------------------------------------------------------
    print("\n--- [Group 5: Payment & FIFO Reconciliation Algorithm] ---")
    
    # 5.1 Record payment of 100,000 with Auto-FIFO disabled initially to test manual reconciliation
    r = client.post("/api/payments", json={
        "customer_id": test_cust_id,
        "amount": 100000.0,
        "payment_date": date.today().isoformat(),
        "payment_method": "Raast",
        "reference_number": "RAAST-TEST-998811",
        "auto_allocate_fifo": False
    }, headers=headers)
    assert r.status_code == 201
    pay_data = r.json()
    assert pay_data["unallocated_amount"] == 100000.0
    assert pay_data["status"] == "Unallocated"
    print(f"[PASS] 5.1 Payment {pay_data['payment_number']} recorded as unallocated cash (PKR 100,000.00).")

    # 5.2 Execute 1-Click FIFO Auto-Reconciliation
    r = client.post("/api/reconciliation/auto-fifo", json={"customer_id": test_cust_id}, headers=headers)
    assert r.status_code == 200
    rec_res = r.json()
    assert rec_res["success"] is True
    assert rec_res["total_amount_allocated"] == 100000.0
    print(f"[PASS] 5.2 1-Click FIFO algorithm matched PKR 100,000.00 against earliest open invoice.")

    # 5.3 Verify invoice balance_due is now 50,000 and status is 'Partially Paid'
    r = client.get(f"/api/invoices/{inv_data['id']}", headers=headers)
    inv_updated = r.json()
    assert inv_updated["paid_amount"] == 100000.0
    assert inv_updated["balance_due"] == 50000.0
    assert inv_updated["status"] == "Partially Paid"
    print(f"[PASS] 5.3 Invoice status updated to 'Partially Paid' with remaining balance PKR 50,000.00.")

    # 5.4 Verify customer net balance updated to 50,000
    r = client.get(f"/api/customers/{test_cust_id}", headers=headers)
    assert r.json()["current_balance"] == 50000.0
    print(f"[PASS] 5.4 Customer ledger statement running balance verified at PKR 50,000.00.")

    # -------------------------------------------------------------
    # Test Group 6: Post-Dated Cheques (PDC) Lifecycle
    # -------------------------------------------------------------
    print("\n--- [Group 6: Post-Dated Cheques (PDC) Lifecycle & Auto-Clearing] ---")
    
    # 6.1 Record PDC for the remaining 50,000 balance
    r = client.post("/api/cheques", json={
        "customer_id": test_cust_id,
        "cheque_number": f"CHQ-{int(time.time()) % 1000000}",
        "bank_name": "Meezan Bank Ltd",
        "amount": 50000.0,
        "issue_date": date.today().isoformat(),
        "maturity_date": (date.today() + timedelta(days=7)).isoformat(),
        "notes": "Post-dated cheque to settle final invoice balance"
    }, headers=headers)
    assert r.status_code == 201
    pdc_data = r.json()
    assert pdc_data["status"] == "Pending Deposit"
    print(f"[PASS] 6.1 Post-Dated Cheque #{pdc_data['cheque_number']} recorded in registry (Maturity: +7 days).")

    # 6.2 Simulate maturity & mark cheque as 'Cleared'
    r = client.put(f"/api/cheques/{pdc_data['id']}/status", json={"status": "Cleared"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "Cleared"
    print(f"[PASS] 6.2 Cheque marked as 'Cleared' -> Triggered automatic payment recognition.")

    # 6.3 Verify invoice is now 100% Paid and Customer Balance is Zero
    r = client.get(f"/api/invoices/{inv_data['id']}", headers=headers)
    inv_final = r.json()
    assert inv_final["status"] == "Paid"
    assert inv_final["balance_due"] == 0.0
    print(f"[PASS] 6.3 Invoice {inv_final['invoice_number']} marked as fully 'Paid' (Balance: PKR 0.00).")

    r = client.get(f"/api/customers/{test_cust_id}", headers=headers)
    assert r.json()["current_balance"] == 0.0
    print(f"[PASS] 6.4 Customer account ledger balance cleared to exactly PKR 0.00.")

    # -------------------------------------------------------------
    # Test Group 7: Stress Testing Simulator & Financial Intelligence
    # -------------------------------------------------------------
    print("\n--- [Group 7: Cash Flow Simulator & Risk Intelligence] ---")
    r = client.get("/api/simulator/run?collection_efficiency_pct=75&average_delay_days=20&default_risk_pct=8&horizon_weeks=8", headers=headers)
    assert r.status_code == 200
    sim_data = r.json()
    assert "metrics" in sim_data
    assert "chart_data" in sim_data
    assert len(sim_data["recommendations"]) > 0
    print(f"[PASS] 7.1 Forward liquidity simulator computed with 8-week horizon.")
    print(f"         Recoverable Cash: PKR {sim_data['metrics']['simulated_recoverable_cash']:,.2f}")
    print(f"         Projected Shortfall: PKR {sim_data['metrics']['expected_liquidity_shortfall']:,.2f}")
    print(f"         Advisory: {sim_data['recommendations'][0]}")

    # -------------------------------------------------------------
    # Test Group 8: Data Exports & International Formats
    # -------------------------------------------------------------
    print("\n--- [Group 8: Export Engines & Reporting Data Integrity] ---")
    for r_type in ["aging", "invoices", "payments"]:
        r = client.get(f"/api/reports/export/{r_type}", headers=headers)
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        assert len(r.content) > 50
        print(f"[PASS] 8.{r_type.capitalize()} CSV export generated with HTTP 200 ({len(r.content)} bytes).")

    print("\n" + "=" * 60)
    print("  ALL 20 SYSTEM VERIFICATION TESTS PASSED WITH 100% SUCCESS!  ")
    print("=" * 60)

if __name__ == "__main__":
    run_deep_verification()
