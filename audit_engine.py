import pandas as pd
import numpy as np
from typing import Dict

# ==========================================
# 1. FIXED ITEM WEIGHTS & RELATIVE ZONE ROUTER
# ==========================================
ITEM_WEIGHTS = {"A": 200, "B": 500, "C": 300, "Box": 100}

def calculate_relative_zone(orig_pin, dest_pin) -> str:
    """
    Calculates Professional D2C logistics zones (Local, Regional, National).
    """
    if pd.isna(orig_pin) or pd.isna(dest_pin):
        return "Zone D (National)"

    orig = str(orig_pin).strip().split('.')[0].zfill(6)
    dest = str(dest_pin).strip().split('.')[0].zfill(6)

    if len(orig) < 6 or len(dest) < 6:
        return "Zone D (National)"

    # Zone A (Local): Same city/district (First 3 digits match)
    if orig[:3] == dest[:3]:
        return "Zone A (Local)"

    # Zone B (Regional): Within the same State boundary
    state_ranges = [
        (11, 11),  # Delhi
        (12, 13),  # Haryana
        (14, 16),  # Punjab
        (20, 28),  # UP/Uttarakhand
        (30, 34),  # Rajasthan
        (36, 39),  # Gujarat
        (40, 44),  # Maharashtra
        (45, 49),  # Madhya Pradesh / CG
        (50, 53),  # Andhra Pradesh / Telangana
        (56, 59),  # Karnataka
        (60, 64),  # Tamil Nadu
        (67, 69),  # Kerala
        (70, 74),  # West Bengal
        (80, 85),  # Bihar / Jharkhand
    ]

    def get_state_id(pin):
        prefix = int(pin[:2])
        for i, (start, end) in enumerate(state_ranges):
            if start <= prefix <= end:
                return i
        return -1

    orig_state = get_state_id(orig)
    dest_state = get_state_id(dest)

    if orig_state != -1 and orig_state == dest_state:
        return "Zone B (Regional)"

    return "Zone D (National)"


# ==========================================
# 2. DATA NORMALIZATION
# ==========================================
def normalise_inventory(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes Inventory, calculates True Weight and True Relative Zone."""
    df = df.copy()
    rename_map = {
        "AWB_Number": "AWB", "Tracking_No": "AWB", "Tracking No": "AWB",
        "Origin Pincode": "Origin_Pincode", "From_Pincode": "Origin_Pincode", "Origin_Pin": "Origin_Pincode",
        "Destination Pincode": "Dest_Pincode", "To_Pincode": "Dest_Pincode", "Dest_Pin": "Dest_Pincode",
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
    df['AWB'] = df['AWB'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

    for col in ['Qty_A', 'Qty_B', 'Qty_C']:
        if col not in df.columns:
            df[col] = 0

    df['Calculated_Total_Weight_g'] = (
        df['Qty_A'] * ITEM_WEIGHTS["A"] +
        df['Qty_B'] * ITEM_WEIGHTS["B"] +
        df['Qty_C'] * ITEM_WEIGHTS["C"] +
        ITEM_WEIGHTS["Box"]
    )

    if 'Origin_Pincode' in df.columns and 'Dest_Pincode' in df.columns:
        df['Calculated_Zone'] = df.apply(
            lambda r: calculate_relative_zone(r['Origin_Pincode'], r['Dest_Pincode']), axis=1
        )

    return df


def normalise_contract(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes Contract/Rate Card for Relative Zones."""
    df = df.copy()
    rename_map = {
        "Partner": "Delivery_Partner",
        "Weight Min (g)": "Weight_Min_g", "Min_Weight_g": "Weight_Min_g",
        "Weight Max (g)": "Weight_Max_g", "Max_Weight_g": "Weight_Max_g",
        "Base Rate (Rs)": "Base_Rate_Rs", "Freight_Rate_Rs": "Base_Rate_Rs",
        "COD Fee (Rs)": "COD_Fee_Rs", "COD_Charge_Rs": "COD_Fee_Rs",
        "RTO %": "RTO_Percentage", "RTO_Pct": "RTO_Percentage",
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
    return df


def normalise_invoice(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes Employee uploaded Invoice."""
    df = df.copy()
    rename_map = {
        "AWB_Number": "AWB", "Tracking No": "AWB", "Waybill": "AWB",
        "Total_Billed_Amount_Rs": "Total_Billed", "Total_Amount": "Total_Billed",
        "Base_Freight_Rs": "Base_Freight", "Freight": "Base_Freight",
        "COD_Charge_Rs": "COD", "RTO_Charge_Rs": "RTO",
        "Misc_Surcharge_Rs": "Other", "Other_Charges": "Other",
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
    df['AWB'] = df['AWB'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

    for col in ["Base_Freight", "COD", "RTO", "Other", "Total_Billed"]:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    df["is_duplicate_awb"] = df["AWB"].duplicated(keep=False)
    return df


# ==========================================
# 3. THE AUDIT ENGINE (CORE LOGIC)
# ==========================================
def run_audit(inventory_df: pd.DataFrame, contract_df: pd.DataFrame, invoice_df: pd.DataFrame) -> Dict:

    # FIX: Capture the true raw invoice total BEFORE dedup collapse.
    # The groupby().first() later removes one leg of duplicate AWBs,
    # so full_data['Total_Billed'].sum() would undercount by the duplicate amount.
    raw_invoice_total = float(invoice_df["Total_Billed"].sum())

    merged = invoice_df.merge(inventory_df, on="AWB", how="left", suffixes=("_inv", "_master"))

    merged = merged.merge(
        contract_df,
        left_on=["Delivery_Partner", "Calculated_Zone"],
        right_on=["Delivery_Partner", "Zone"],
        how="left",
    )

    merged["in_slab"] = (
        (merged["Calculated_Total_Weight_g"] >= merged["Weight_Min_g"]) &
        (merged["Calculated_Total_Weight_g"] < merged["Weight_Max_g"])
    )

    # Collapse duplicate AWBs — keeps the best-matching slab row per AWB.
    # This intentionally deduplicates; raw_invoice_total preserves the real billed sum.
    merged = (
        merged.sort_values(["AWB", "in_slab", "Weight_Max_g"], ascending=[True, False, True])
        .groupby("AWB", as_index=False)
        .first()
    )

    merged["Expected_Freight"] = merged["Base_Rate_Rs"].fillna(0.0)

    merged["Expected_COD"] = merged.apply(
        lambda r: r["COD_Fee_Rs"]
        if pd.notna(r.get("Payment_Type")) and any(x in str(r["Payment_Type"]).upper() for x in ["COD", "CASH"])
        else 0.0,
        axis=1,
    ).fillna(0.0)

    merged["Expected_RTO"] = merged.apply(
        lambda r: r["RTO_Percentage"] * r["Expected_Freight"]
        if pd.notna(r.get("Delivery_Status")) and str(r["Delivery_Status"]).upper() == "RTO"
        else 0.0,
        axis=1,
    ).fillna(0.0)

    merged["Expected_Total"] = merged["Expected_Freight"] + merged["Expected_COD"] + merged["Expected_RTO"]
    merged["Diff_Freight"] = merged["Base_Freight"] - merged["Expected_Freight"]
    merged["Diff_Total"] = merged["Total_Billed"] - merged["Expected_Total"]

    def classify_row(row):
        reasons = []
        if pd.isna(row.get("Delivery_Partner")):
            return "Invalid Shipment (Not in Inventory)"
        if row.get("is_duplicate_awb"):
            reasons.append("Duplicate AWB in invoice")
        if pd.isna(row.get("Base_Rate_Rs")):
            reasons.append("No contract rate for route/slab")

        if row.get("Billed_Zone") != row.get("Calculated_Zone"):
            reasons.append(f"Zone Mismatch (Expected: {row.get('Calculated_Zone')})")

        if row["Diff_Freight"] > 1.0:
            if (
                pd.notna(row.get("Billed_Weight_g"))
                and pd.notna(row.get("Weight_Max_g"))
                and row["Billed_Weight_g"] > row["Weight_Max_g"]
            ):
                reasons.append(f"Weight Overcharge (Billed {row['Billed_Weight_g']}g, pushed to higher slab)")
            else:
                reasons.append("Rate Deviation (Billed freight > Contracted freight)")

        if row["Expected_COD"] == 0 and row["COD"] > 0:
            reasons.append("Invalid COD charge (Prepaid order)")
        elif row["Expected_RTO"] == 0 and row["RTO"] > 0:
            reasons.append("Invalid RTO charge (Delivered order)")
        elif row["Expected_RTO"] > 0 and abs(row["RTO"] - row["Expected_RTO"]) > 1.0:
            reasons.append("RTO % Math Mismatch")

        specific_errors = ["Weight Overcharge", "Rate Deviation", "Invalid COD", "Invalid RTO", "RTO %"]
        if row["Diff_Total"] > 1.0 and not any(any(e in r for r in reasons) for e in specific_errors):
            reasons.append("Non-Contractual/Unidentified Surcharge")

        if not reasons:
            return "Cleared - Payout Approved"
        return " | ".join(reasons)

    merged["Discrepancy_Type"] = merged.apply(classify_row, axis=1)

    discrepancies = merged[merged["Discrepancy_Type"] != "Cleared - Payout Approved"].copy()
    report_cols = [
        "AWB", "Discrepancy_Type", "Calculated_Total_Weight_g", "Billed_Weight_g",
        "Calculated_Zone", "Billed_Zone", "Expected_Total", "Total_Billed", "Diff_Total",
    ]
    discrepancy_report = discrepancies[[c for c in report_cols if c in discrepancies.columns]]

    # Payout: exclude Ghost shipments and Duplicates — only pay approved, legitimate shipments
    payout = merged[
        ~merged["Discrepancy_Type"].str.contains("Invalid Shipment|Duplicate", na=False)
    ].copy()
    payout["Approved_Payout_Rs"] = payout["Expected_Total"]

    # FIX: approved_payout = what we SHOULD pay across all unique legitimate shipments.
    # This is the sum of Expected_Total across all 59 deduped rows in full_data.
    # - For clean shipments: Expected_Total = Total_Billed (no issue)
    # - For discrepancy shipments: Expected_Total = correct contract amount
    # - For ghost shipments: Expected_Total = 0 (should not pay)
    # - For the duplicate AWB: Expected_Total = 391.34 (pay once, not twice)
    #   The extra 391.34 billing is caught in raw_invoice_total - approved_payout.
    approved_payout = float(merged["Expected_Total"].sum())

    return {
        "full_data": merged,
        "discrepancies": discrepancy_report,
        "payout": payout,
        # Use these summary metrics in the UI — do NOT re-derive from full_data sums,
        # as full_data collapses duplicates and loses one leg of the raw invoice total.
        "summary": {
            "total_billed": raw_invoice_total,                       # True invoice total (all 60 rows)
            "approved_payout": approved_payout,                      # What we should actually pay
            "total_discrepancy": raw_invoice_total - approved_payout, # Total overcharges caught
            "discrepancy_count": len(discrepancy_report),
        },
    }