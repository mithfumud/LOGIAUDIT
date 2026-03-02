# 🌿 LogiAudit: Logistics Billing Intelligence

LogiAudit is a deterministic, enterprise-grade logistics reconciliation engine built to identify billing leakages, fraud, and overcharges from delivery partners. By cross-referencing Courier Invoices against agreed Rate Contracts and internal Inventory ground-truth, LogiAudit catches discrepancies in seconds with **Zero AI Hallucinations**.

---

# LogiAudit: Smart Logistics Billing Checker

LogiAudit is an automated tool built to catch billing errors, ghost shipments, and hidden fees from delivery partners. By comparing courier invoices against your company's actual shipment data and agreed-upon contracts, this app delivers 100% mathematical accuracy to protect profit margins.

## The Business Problem
E-commerce brands lose thousands of dollars every month to tiny, easily missed errors in courier bills—like a 200g package being charged as a 500g package, or a local delivery being billed at expensive national rates. 

Manually checking these massive spreadsheets takes days and is prone to human error. LogiAudit replaces this manual work with a fast, automated system that processes thousands of rows in seconds and tells you exactly how much you are being overcharged.

## How It Works

The application uses a simple two-step process to keep your data secure and accurate:

1. **Admin Portal (Setting the Baseline):** The Operations team uploads the internal Master Inventory. The system automatically calculates exactly how much each package *should* weigh (based on the items inside) and maps out the correct delivery zones using Indian postal codes.
2. **Employee Portal (Running the Audit):** The Finance team uploads the agreed-upon Rate Contract and the monthly Courier Bill. The system instantly cross-checks every single charge on the bill against the internal data.

## What the System Catches
The audit runs a strict 8-point check to flag the following discrepancies:
* 📦 **Weight Overcharges:** The courier charged for a heavier weight bracket than the package actually was.
* 🗺️ **Zone Mismatches:** A local or regional package was wrongly billed at a higher long-distance rate.
* 👻 **Ghost Shipments:** The courier billed you for tracking numbers that do not exist in your company's records.
* 👯 **Duplicate AWBs:** The courier charged you twice for the same package on the same invoice.
* 💸 **Invalid COD Fees:** Cash-on-Delivery handling fees were applied to orders that were already prepaid.
* 🔄 **Invalid RTO Charges:** Return-to-Origin fees were applied to orders that were successfully delivered to the customer.
* 📉 **Rate Deviations:** The base delivery price on the bill doesn't match the price agreed upon in the contract.

## Tech Stack
* **Frontend Interface:** Streamlit (Python)
* **Data Processing Engine:** Pandas, NumPy
* **File Handling:** OpenPyXL, BytesIO (Fast, in-memory Excel generation)

---

## 🧪 How to Test the Application

To evaluate the app yourself, you will need the sample Excel files. **Please download the files from the `Excel_data` folder in this GitHub repository** to your computer first.

**Step 1: Set the Baseline (Admin Portal)**
1. Open the live application and go to the **Admin Setup** tab on the left sidebar.
2. Upload the `inventory_master.xlsx` file (downloaded from the `Excel_data` folder). The engine will instantly read the shipments and establish the true weights and zones.

**Step 2: Run the Audit (Employee Portal)**
1. Go to the **Run Audit** tab.
2. Upload the `contract.xlsx` file into the Rate Contract dropzone.
3. Upload the `invoice.xlsx` file into the Logistics Invoice dropzone.
4. Click **Run Automated Audit**. 

The app will immediately generate a financial summary, a breakdown of the errors, a "Scorecard" showing how reliable the partner is, and clean payout files you can download.

---

## Behind the Scenes (Product & Engineering Decisions)

* **100% Accuracy over AI Guesswork:** We intentionally did not use AI or Large Language Models (LLMs) for the auditing. Financial checks need absolute mathematical certainty. The system uses strict, automated data rules to guarantee there are zero "hallucinations" or false guesses.
* **Smart Geography Routing:** Indian postal codes can be tricky (for example, Mumbai and Pune have completely different pin code prefixes but belong to the same "Regional" state bracket). We built custom logic that maps pin codes to actual state boundaries so couriers cannot overcharge for distance.
* **Focusing on Real Losses:** The system is smart enough to ignore harmless mistakes. If a courier bills for 400g instead of 200g, but *both* weights cost the exact same amount under your contract, the app clears it. This ensures your finance team doesn't waste time chasing zero-dollar issues.

---

## 🚀 Future Roadmap

While this version successfully proves the core auditing logic, scaling this for a large enterprise would involve the following upgrades:

* **Cloud Database Storage:** Moving from temporary session storage to a secure database. This would allow the business to track long-term trends and see which delivery partners make the most "mistakes" quarter-over-quarter.
* **Automated Courier Connections (APIs):** Replacing the manual Excel uploads by connecting directly to the courier's billing systems (like BlueDart or Delhivery) to pull in invoices automatically as they are generated.
* **User Access Controls:** Adding secure login screens so only authorized Operations Admins can upload the source of truth, while Finance Employees can only execute the audits and download reports.
* **Smart Partner Allocation:** Using the historical audit data to build a tool that automatically recommends the most cost-effective and honest delivery partner for future shipments based on specific cities or pin codes.
