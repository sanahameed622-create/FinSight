# FinSight — AI-Powered Financial Intelligence & Automated Payment Reconciliation Platform

> **Product Positioning:** Enterprise-grade Financial Management & Payment Reconciliation SaaS designed for B2B Suppliers, FMCG Distributors, Wholesalers, and Merchants.  
> **Global Compliance:** Built in accordance with standard GAAP / IFRS accounting standards (Customer Statements of Account, Accounts Receivable Aging, Running Ledger Balances, and Multi-Currency architecture).

---

## 🌟 Flagship Capabilities & Features

### 1. Smart Payment Reconciliation Engine (FIFO & Manual Matrix)
* **1-Click Auto-Reconciliation:** Automatically applies First-In First-Out (FIFO) matching algorithms to pair unallocated customer receipts with earliest open invoices chronologically.
* **Manual Allocation Matrix:** Link custom payment sums to specific invoice lines with real-time balance calculations.
* **Elimination of Unallocated Cash:** Prevents unapplied bank credits from remaining idle, ensuring accurate customer statements.

### 2. Accounts Receivable (AR) Ledger & Aging Analytics
* **Chronological Statement of Account:** Complete audit trail of customer transactions detailing Invoiced Debits, Payment Credits, and Running Ledger Balances.
* **Maturity Aging Buckets:** Granular exposure analysis: **Current (0–30 Days)**, **31–60 Days**, **61–90 Days**, and **Critical Overdue (90+ Days)**.
* **Debtor Risk Classification:** Dynamic risk tiers (Low, Medium, High) based on aging maturity and credit limit utilization.

### 3. 📱 1-Click WhatsApp Statement & Invoice Dispatcher
* Instantly generate and transmit personalized, formatted Statements of Account and Commercial Invoices directly to customer WhatsApp contacts with pre-composed payment remittance details.

### 4. 🖨️ Print-Ready Commercial Invoices with Instant Payment QR Code
* High-resolution, print-optimized A4 layout featuring company branding, tax registration, customer billing details, itemized goods, and authorized signature lines.
* **Instant Digital Payment QR Code:** Embedded on every invoice and statement for rapid mobile banking / Raast remittance.

### 5. 🏦 Post-Dated Cheques (PDC) Registry & Maturity Tracker
* Full management lifecycle for incoming customer cheques: Drawee Bank, Cheque Number, Maturity / Deposit Due Date, and Status (Pending Deposit, Deposited, Cleared, Bounced).
* **1-Click Cheque Clearance:** Marking a PDC as *Cleared* automatically issues a recognized payment and auto-reconciles open invoices via FIFO!

### 6. 📦 Warehouse Inventory & Stock Control
* Comprehensive SKU catalogue: Stock on Hand, Unit Cost, Selling Price, and Reorder Thresholds.
* **Invoicing Auto-Deduction:** Generating sales invoices automatically deducts product inventory in real-time, triggering low-stock alerts.

### 7. 🎯 Cash Flow & Liquidity Stress Simulator
* Interactive parameter controls: **On-Time Collection Rate (%)**, **Average Payment Delay (Days)**, **Bad Debt / Default Risk (%)**, and **Forecast Horizon (Weeks)**.
* Visualizes contractual cash expectations against simulated stress-tested realization curves.
* Actionable working-capital advisory recommendations for inventory restocking safety.

---

## 🏗️ Technical Architecture & File Directory

```
FinSight/
├── frontend/
│   ├── index.html             # Landing & Overview page
│   ├── login.html             # Secure login screen with 1-click Demo Fill
│   ├── register.html          # Enterprise business onboarding
│   ├── dashboard.html         # Executive KPI dashboard & Chart.js visualizations
│   ├── customers.html         # Customer Accounts Directory & Statement modal
│   ├── invoices.html          # Invoices ledger & dynamic line-item builder
│   ├── payments.html          # Direct receipts & Post-Dated Cheques (PDC) registry
│   ├── inventory.html         # Warehouse SKU catalogue & stock adjustment
│   ├── reconciliation.html    # Dual-pane matching workspace & 1-click FIFO engine
│   ├── simulator.html         # Forward liquidity stress testing & recovery simulator
│   ├── reports.html           # Aging matrix & Statement CSV exporter
│   ├── settings.html          # Enterprise config, localization & DBMS status
│   ├── css/
│   │   ├── style.css          # Design system tokens, typography, layout, print styles
│   │   ├── dashboard.css      # KPI grid, AI widget & Chart containers
│   │   ├── forms.css          # Inputs, sliders, search & dynamic line items
│   │   └── responsive.css     # Mobile drawer navigation & breakpoint adjustments
│   └── js/
│       ├── api.js             # Centralized fetch wrapper & formatPKR helpers
│       ├── auth.js            # JWT session management & page protection guards
│       ├── dashboard.js       # Live metrics, Chart.js cash trend & AI insights
│       ├── customers.js       # Customer CRUD & Statement renderer
│       ├── invoices.js        # Invoice creation, item totals & WhatsApp dispatch
│       ├── payments.js        # Payment recording & PDC status management
│       ├── inventory.js       # Stock level tracking & SKU catalogue
│       ├── reconciliation.js  # Dual-pane matching workspace & 1-click FIFO trigger
│       ├── simulator.js       # Interactive sliders & simulation projections
│       ├── reports.js         # Aging matrix & Statement CSV exporter
│       └── validation.js      # Modal controls & Toast alert engine
│
├── backend/
│   ├── main.py                # FastAPI ASGI application & static route serving
│   ├── config.py              # Environment configuration & DB connection URL
│   ├── database.py            # SQLAlchemy 2.0 ORM engine & SessionLocal
│   ├── dependencies.py        # Bearer token JWT authentication dependency
│   ├── seeder.py              # Pre-seeded realistic B2B wholesale demo dataset
│   ├── models/                # User, Business, Customer, Invoice, Payment, Product, PostDatedCheque, Allocation, ActivityLog
│   ├── schemas/               # Pydantic v2 schemas for API input validation
│   ├── routes/                # Auth, Customers, Invoices, Payments, Cheques, Products, Reconciliation, Dashboard, Reports, Simulator
│   ├── services/              # Business logic (Reconciliation, Reports, Simulator, AI Insights)
│   └── utils/                 # Security (Salted PBKDF2 cryptography & JWT encoding)
│
├── tests/
│   └── test_api.py            # 14-step end-to-end integration test suite
├── run.py                     # One-click startup runner
├── requirements.txt           # Python dependency manifest
└── README.md                  # Complete documentation
```

---

## 🚀 Execution Instructions

### 1. Prerequisites
* Python 3.10 or newer.

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Run the Application Server
```bash
python run.py
```
Or with uvicorn:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 4. Access URLs
* **Web Portal:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Swagger API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Demo Credentials:** `admin@finsight.pk` / `admin123` *(or click "Fill Demo" on the sign-in page)*

---

## 🧪 Automated Integration Tests

Run the complete 14-step automated verification suite:
```bash
python tests/test_api.py
```

Expected result:
```
[PASS] 1. Health check
[PASS] 2. Login successful. Token generated.
[PASS] 3. Profile verified
[PASS] 4. Retrieved customers
[PASS] 5. Statement of Account generated
[PASS] 6. Retrieved invoices
[PASS] 7. Retrieved payments
[PASS] 8. Smart FIFO Auto-Reconciliation executed
[PASS] 9. Dashboard stats & AI Health Score
[PASS] 10. Aging report verified
[PASS] 11. Cash Flow Simulator verified
[PASS] 12. Product catalogue verified (5 active SKUs)
[PASS] 13. Post-Dated Cheques verified
[PASS] 14. Cheque clearance & automated credit conversion
>>> ALL 14 TESTS PASSED WITH 100% SUCCESS! <<<
```
