import pandas as pd
import random
import os
from datetime import datetime, timedelta

print("🚀 Starting Enterprise-Grade Logistics Data Generator...")

# ==========================================
# 1. CONFIGURATION & CONSTANTS
# ==========================================
NUM_SHIPMENTS = 250  
PARTNERS = ["Delhivery", "BlueDart", "Ecom Express", "Shadowfax"]

# Professional D2C Relative Zones
ZONES = ["Zone A (Local)", "Zone B (Regional)", "Zone D (National)"]

# Structured State & City Pincode Pool mapping directly to real Indian Postal Index boundaries
STATE_CITIES = {
    "Maharashtra": {  # State Prefix Range: 40-44
        "Mumbai": [400001, 400050, 400099],
        "Pune": [411001, 411038, 411045],
        "Nagpur": [440001, 440010, 440022]
    },
    "Karnataka": {    # State Prefix Range: 56-59
        "Bangalore": [560001, 560010, 560034],
        "Mysore": [570001, 570020]
    },
    "Delhi": {        # State Prefix Range: 11
        "New_Delhi": [110001, 110020, 110055]
    },
    "Tamil_Nadu": {   # State Prefix Range: 60-64
        "Chennai": [600001, 600028]
    }
}

# Fixed Product Weights
ITEM_WEIGHTS = {"A": 200, "B": 500, "C": 300, "Box": 100}

# Standard D2C Contract Slabs
SLABS = [
    {"min": 0, "max": 500, "base_A": 30, "base_B": 45, "base_D": 70},
    {"min": 500, "max": 1000, "base_A": 50, "base_B": 80, "base_D": 120},
    {"min": 1000, "max": 2000, "base_A": 90, "base_B": 140, "base_D": 200},
    {"min": 2000, "max": 5000, "base_A": 160, "base_B": 240, "base_D": 350},
    {"min": 5000, "max": 10000, "base_A": 300, "base_B": 450, "base_D": 600}
]

OUT_DIR = "dummy_data"
os.makedirs(OUT_DIR, exist_ok=True)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def generate_random_date(start_date: str, days_range: int) -> str:
    """Generates a random dispatch date."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    return (start + timedelta(days=random.randint(0, days_range))).strftime("%Y-%m-%d")

def get_pincodes_for_zone(target_zone: str):
    """Dynamically fetches two valid pincodes that mathematically satisfy the target zone."""
    if target_zone == "Zone A (Local)":
        # Same City (First 3 digits will match)
        state = random.choice(list(STATE_CITIES.keys()))
        city = random.choice(list(STATE_CITIES[state].keys()))
        orig = random.choice(STATE_CITIES[state][city])
        dest = random.choice(STATE_CITIES[state][city])
        return orig, dest
        
    elif target_zone == "Zone B (Regional)":
        # Same State, Different City (First 2 digits in same bracket, first 3 differ)
        # We only pick from states that have more than 1 city listed (MH or KA)
        multi_city_states = [s for s in STATE_CITIES.keys() if len(STATE_CITIES[s]) > 1]
        state = random.choice(multi_city_states)
        cities = list(STATE_CITIES[state].keys())
        city1, city2 = random.sample(cities, 2)
        orig = random.choice(STATE_CITIES[state][city1])
        dest = random.choice(STATE_CITIES[state][city2])
        return orig, dest
        
    else:
        # Zone D (National) - Different States
        states = list(STATE_CITIES.keys())
        state1, state2 = random.sample(states, 2)
        city1 = random.choice(list(STATE_CITIES[state1].keys()))
        city2 = random.choice(list(STATE_CITIES[state2].keys()))
        orig = random.choice(STATE_CITIES[state1][city1])
        dest = random.choice(STATE_CITIES[state2][city2])
        return orig, dest

# ==========================================
# 3. BUILD THE INVENTORY (The Source of Truth)
# ==========================================
print("📦 Building Master Inventory with rigorous State Boundaries...")
inventory_list = []

for i in range(1, NUM_SHIPMENTS + 1):
    target_zone = random.choice(ZONES)
    orig_pin, dest_pin = get_pincodes_for_zone(target_zone)
    
    qty_a, qty_b, qty_c = random.randint(0, 4), random.randint(0, 3), random.randint(0, 3)
    if (qty_a + qty_b + qty_c) == 0: 
        qty_a = 1  
    
    true_w = (qty_a * ITEM_WEIGHTS["A"]) + (qty_b * ITEM_WEIGHTS["B"]) + (qty_c * ITEM_WEIGHTS["C"]) + ITEM_WEIGHTS["Box"]
    
    inventory_list.append({
        "AWB": f"AWB-{random.randint(10000, 99999)}-{i}", 
        "Order_Date": generate_random_date("2026-02-01", 28),
        "Delivery_Partner": random.choice(PARTNERS),
        "Origin_Pincode": orig_pin,
        "Dest_Pincode": dest_pin,
        "Qty_A": qty_a, 
        "Qty_B": qty_b, 
        "Qty_C": qty_c,
        "Payment_Type": random.choices(["Prepaid", "COD"], weights=[0.6, 0.4])[0],
        "Delivery_Status": random.choices(["Delivered", "RTO"], weights=[0.88, 0.12])[0],
        "_True_Weight": true_w,       # Hidden tracker
        "_Target_Zone": target_zone   # Hidden tracker
    })

df_inventory = pd.DataFrame(inventory_list)
df_inv_out = df_inventory.drop(columns=["_True_Weight", "_Target_Zone"])
df_inv_out.to_excel(os.path.join(OUT_DIR, "inventory_master.xlsx"), index=False)
print(f"✅ Created inventory_master.xlsx ({NUM_SHIPMENTS} rows)")

# ==========================================
# 4. BUILD CONTRACTS & INVOICES PER PARTNER
# ==========================================
print("📄 Generating Contracts and correlating Invoices...")

for partner in PARTNERS:
    partner_inventory = df_inventory[df_inventory["Delivery_Partner"] == partner].copy()
    if partner_inventory.empty: continue
    
    partner_markup = random.uniform(0.95, 1.15)
    cod_flat = random.choice([20.0, 25.0, 30.0, 40.0])
    rto_pct = random.choice([0.40, 0.50, 0.60])
    
    # --- A. GENERATE CONTRACT ---
    contract_rows = []
    for slab in SLABS:
        for zone in ZONES:
            if zone == "Zone A (Local)": base = slab["base_A"]
            elif zone == "Zone B (Regional)": base = slab["base_B"]
            else: base = slab["base_D"]
            
            contract_rows.append({
                "Delivery_Partner": partner,
                "Zone": zone,
                "Weight_Min_g": slab["min"], 
                "Weight_Max_g": slab["max"],
                "Base_Rate_Rs": round(base * partner_markup, 2),
                "COD_Fee_Rs": cod_flat, 
                "RTO_Percentage": rto_pct
            })
                
    pd.DataFrame(contract_rows).to_excel(os.path.join(OUT_DIR, f"contract_{partner}.xlsx"), index=False)
    
    # --- B. GENERATE CORRELATED INVOICE ---
    invoice_rows = []
    for _, row in partner_inventory.iterrows():
        true_w = row["_True_Weight"]
        target_zone = row["_Target_Zone"]
        
        # 1. Perfect Expected Baseline
        slab_rate = next(r["Base_Rate_Rs"] for r in contract_rows if r["Zone"] == target_zone and r["Weight_Min_g"] <= true_w < r["Weight_Max_g"])
        
        expected_freight = slab_rate
        expected_cod = cod_flat if row["Payment_Type"] == "COD" else 0.0
        expected_rto = round(expected_freight * rto_pct, 2) if row["Delivery_Status"] == "RTO" else 0.0
        
        billed_w = true_w
        billed_freight = expected_freight
        billed_cod = expected_cod
        billed_rto = expected_rto
        billed_zone = target_zone
        misc = 0.0
        
        # 2. Inject Controlled Chaos (35% chance)
        error_type = random.choices(
            ["Perfect", "Weight_Fraud", "Fake_COD", "Fake_RTO", "Surcharge", "Zone_Mismatch"], 
            weights=[0.65, 0.10, 0.08, 0.02, 0.10, 0.05]
        )[0]
        
        if error_type == "Weight_Fraud":
            billed_w = true_w + random.randint(300, 1500) 
            try: 
                billed_freight = next(r["Base_Rate_Rs"] for r in contract_rows if r["Zone"] == target_zone and r["Weight_Min_g"] <= billed_w < r["Weight_Max_g"])
            except StopIteration: 
                billed_freight += 100 
                
        elif error_type == "Fake_COD" and row["Payment_Type"] == "Prepaid":
            billed_cod = cod_flat
            
        elif error_type == "Fake_RTO" and row["Delivery_Status"] == "Delivered":
            billed_rto = round(expected_freight * rto_pct, 2) 
            
        elif error_type == "Surcharge":
            misc = round(random.uniform(10.0, 50.0), 2)
            
        elif error_type == "Zone_Mismatch":
            wrong_zones = [z for z in ZONES if z != target_zone]
            billed_zone = random.choice(wrong_zones)
            billed_freight = next(r["Base_Rate_Rs"] for r in contract_rows if r["Zone"] == billed_zone and r["Weight_Min_g"] <= billed_w < r["Weight_Max_g"])

        total_billed = billed_freight + billed_cod + billed_rto + misc
        
        invoice_rows.append({
            "Tracking No": row["AWB"], 
            "Shipment_Date": generate_random_date(row["Order_Date"], 5),
            "Origin_Pincode": row["Origin_Pincode"], 
            "Dest_Pincode": row["Dest_Pincode"],
            "Billed_Weight_g": billed_w, 
            "Billed_Zone": billed_zone,
            "Base_Freight_Rs": billed_freight, 
            "COD_Charge_Rs": billed_cod,
            "RTO_Charge_Rs": billed_rto, 
            "Misc_Surcharge_Rs": misc,
            "Total_Amount": round(total_billed, 2)
        })
    
    # 3. Inject Structural Edge Cases
    if len(invoice_rows) > 0:
        duplicate = invoice_rows[random.randint(0, len(invoice_rows)-1)].copy()
        invoice_rows.append(duplicate) 
        
        ghost = invoice_rows[0].copy()
        ghost["Tracking No"] = f"AWB-GHOST-{random.randint(1000,9999)}"
        invoice_rows.append(ghost)
        
    df_invoice = pd.DataFrame(invoice_rows)
    df_invoice.to_excel(os.path.join(OUT_DIR, f"invoice_{partner}.xlsx"), index=False)
    print(f"✅ Created {partner} Files -> Contract: {len(contract_rows)} routes | Invoice: {len(invoice_rows)} shipments")

print("\n🎉 Massive Dynamic Dataset Generated! Check the 'dummy_data' folder.")