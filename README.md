# 🌿 LogiAudit: Logistics Billing Intelligence
**Developed for Mosaic Wellness**

LogiAudit is a deterministic, enterprise-grade logistics reconciliation engine built to identify billing leakages, fraud, and overcharges from delivery partners. By cross-referencing Courier Invoices against agreed Rate Contracts and internal Inventory ground-truth, LogiAudit catches discrepancies in seconds with **Zero AI Hallucinations**.

---

## 🚀 The Problem & The Solution
D2C companies lose thousands of dollars monthly to tiny, easily missed errors in logistics invoices (e.g., 200g bumped to 500g, intra-state shipments billed as national, double-billing, or ghost AWBs).

**LogiAudit** solves this using a strict, mathematical rules engine. It acts as a "2-Faced" portal:
1. **Admin Portal:** Establishes the "Source of Truth" by uploading the master inventory. The engine auto-calculates the *True Weight* of packages based on SKUs and mathematically deduces the *Relative Zone* (Local, Regional, National) based on Indian Postal State Boundaries.
2. **Employee Portal:** Employees upload the monthly partner invoice and the agreed rate card. The engine cross-checks every single line item and outputs the exact Approved Payout and an itemized Discrepancy Report.

---

## 🔍 What We Catch (The 8-Point Audit)
The deterministic engine actively flags:
* 📦 **Weight Overcharges:** Billed weight pushed into a higher, more expensive contract slab.
* 🗺️ **Zone Mismatches:** Local/Regional shipments maliciously or accidentally billed as National.
* 👻 **Ghost Shipments:** AWBs billed by the courier that do not exist in your internal inventory.
* 👯 **Duplicate AWBs:** The exact same shipment billed twice in the same invoice.
* 💸 **Invalid COD Fees:** COD charges applied to Prepaid orders.
* 🔄 **Invalid RTO Charges:** RTO (Return to Origin) fees applied to successfully delivered orders.
* 📉 **Rate Deviations:** Discrepancies between the contract's base rate and the billed base freight.
* ❓ **Unidentified Surcharges:** Hidden padding added to the final bill outside of contractual terms.

---

## 🛠️ Tech Stack
* **Frontend UI:** Streamlit (Python)
* **Data Engine:** Pandas, NumPy
* **File Handling:** OpenPyXL, BytesIO (In-memory Excel generation)

---

## 📂 Project Structure
```text
logi-audit-tool/
│
├── app.py                 # Main Streamlit UI & Routing (Welcome, Admin, Employee, Results, History)
├── audit_engine.py        # Core logic, Zone mathematics, and dataframe normalization
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
