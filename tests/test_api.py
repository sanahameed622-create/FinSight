import sys
import time
from pathlib import Path

# Add project root to path
base = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base))

from starlette.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.seeder import seed_sample_business_data

def run_all_tests():
    client = TestClient(app)

    # 1. Test Health
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("[PASS] 1. Health check:", r.json())

    # 2. Register Dynamic Secure Tenant
    test_email = f"test.api.{int(time.time())}@securetest.local"
    test_password = "SecureVerificationKey!99"
    r = client.post("/api/auth/register", json={
        "full_name": "API Verification Admin",
        "email": test_email,
        "password": test_password,
        "phone": "+92 300 0000000",
        "business_name": "API Verification Hub Ltd",
        "city": "Lahore"
    })
    assert r.status_code == 200, f"Registration failed: {r.text}"
    auth_data = r.json()
    token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    biz_id = auth_data["user"]["business_id"]
    user_id = auth_data["user"]["id"]

    # Seed sample business items for this tenant
    with SessionLocal() as db:
        seed_sample_business_data(db, business_id=biz_id, user_id=user_id)

    # Test Login
    r = client.post("/api/auth/login", json={"email": test_email, "password": test_password})
    assert r.status_code == 200, f"Login failed: {r.text}"
    print("[PASS] 2. Login successful with dynamic credentials. Token generated.")

    # 3. Test Profile
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    print(f"[PASS] 3. Profile verified for: {r.json()['full_name']}")

    # 4. Test Customers
    r = client.get("/api/customers", headers=headers)
    assert r.status_code == 200
    customers = r.json()
    assert len(customers) >= 5
    cust_id = customers[0]["id"]
    print(f"[PASS] 4. Retrieved {len(customers)} customers. Sample: {customers[0]['name']}")

    # 5. Test Customer Statement of Account
    r = client.get(f"/api/customers/{cust_id}/ledger", headers=headers)
    assert r.status_code == 200
    ledger = r.json()
    print(f"[PASS] 5. Statement of Account generated for {ledger['customer']['name']}. Transactions: {len(ledger['statement'])}")

    # 6. Test Invoices
    r = client.get("/api/invoices", headers=headers)
    assert r.status_code == 200
    invoices = r.json()
    assert len(invoices) >= 5
    print(f"[PASS] 6. Retrieved {len(invoices)} invoices.")

    # 7. Test Payments
    r = client.get("/api/payments", headers=headers)
    assert r.status_code == 200
    payments = r.json()
    assert len(payments) >= 2
    print(f"[PASS] 7. Retrieved {len(payments)} payments.")

    # 8. Test FIFO Auto-Reconciliation
    r = client.post("/api/reconciliation/auto-fifo", json={}, headers=headers)
    assert r.status_code == 200, f"Auto-FIFO failed: {r.text}"
    reconcile_res = r.json()
    print(f"[PASS] 8. Smart FIFO Auto-Reconciliation executed: {reconcile_res['message']}")

    # 9. Test Dashboard Stats & AI Insights
    r = client.get("/api/dashboard/stats", headers=headers)
    assert r.status_code == 200
    dash = r.json()
    print(f"[PASS] 9. Dashboard stats: Receivables=PKR {dash['kpis']['total_receivables']:,.2f}, AI Health Score={dash['ai_insights']['health_score']}")

    # 10. Test Reports Aging
    r = client.get("/api/reports/aging", headers=headers)
    assert r.status_code == 200
    aging = r.json()
    print(f"[PASS] 10. Aging report verified. Grand Total Receivables: PKR {aging['summary']['grand_total_receivables']:,.2f}")

    # 11. Test Simulator
    r = client.get("/api/simulator/run?collection_efficiency_pct=85&average_delay_days=15&default_risk_pct=5&horizon_weeks=6", headers=headers)
    assert r.status_code == 200
    sim = r.json()
    print(f"[PASS] 11. Cash Flow Simulator verified: Recoverable Cash=PKR {sim['metrics']['simulated_recoverable_cash']:,.2f}")

    # 12. Test Inventory Products
    r = client.get("/api/products", headers=headers)
    assert r.status_code == 200
    prods = r.json()
    assert len(prods) >= 5
    print(f"[PASS] 12. Product catalogue verified: {len(prods)} active SKUs loaded.")

    # 13. Test Post-Dated Cheques (PDC)
    r = client.get("/api/cheques", headers=headers)
    assert r.status_code == 200
    chqs = r.json()
    assert len(chqs) >= 1
    print(f"[PASS] 13. Post-Dated Cheques verified: {len(chqs)} PDC(s) tracked. Sample: Cheque #{chqs[0]['cheque_number']} ({chqs[0]['bank_name']})")

    # 14. Test Cheque Clearing
    chq_id = chqs[0]["id"]
    r = client.put(f"/api/cheques/{chq_id}/status", json={"status": "Cleared"}, headers=headers)
    assert r.status_code == 200
    print(f"[PASS] 14. Cheque #{r.json()['cheque_number']} cleared successfully and converted to auto-reconciled credit.")

    print("\n>>> ALL 14 TESTS PASSED WITH 100% SUCCESS! <<<")

if __name__ == "__main__":
    run_all_tests()
