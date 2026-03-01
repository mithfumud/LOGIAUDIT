import streamlit as st
import pandas as pd
from io import BytesIO
import datetime
import time
import audit_engine

# ONE set_page_config — expanded, always, forever
st.set_page_config(
    page_title="Mosaic Wellness · LogiAudit",
    layout="wide",
    page_icon="🌿",
    initial_sidebar_state="expanded",
)

# ── Session state ────────────────────────────────────────────────────────
for k, v in {
    "intro_seen":      False,
    "current_page":    "Home",
    "inventory_master": None,
    "audit_results":   None,
    "audit_history":   [],
    "partner_history": {},
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def navigate_to(page):
    st.session_state["current_page"] = page

# ── Global CSS (sidebar NEVER touched for visibility) ────────────────────
st.markdown("""
<style>
/* Remove top bar completely on all pages */
header[data-testid="stHeader"]  { display: none !important; }
footer                           { display: none !important; }

/* Hide ALL collapse/expand toggle buttons — sidebar stays permanently open */
[data-testid="collapsedControl"]        { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
button[data-testid="baseButton-header"] { display: none !important; }

.block-container { padding-top: 0.5rem; padding-bottom: 2rem; max-width: 1280px; }
[data-testid="stAppViewContainer"] { background: #F0F4F8; }

[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #0A2E0F 0%, #1B5E20 60%, #2E7D32 100%) !important;
    min-width: 260px !important; border-right: none;
}
[data-testid="stSidebar"] * { color: #E8F5E9 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.08) !important; color: #E8F5E9 !important;
    border: 1px solid rgba(255,255,255,0.15) !important; border-radius: 8px !important;
    font-weight: 500 !important; padding: 0.55rem 1rem !important;
    transition: all 0.2s ease; width: 100%; text-align: left !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.18) !important;
    border-color: rgba(255,255,255,0.35) !important; transform: translateX(3px);
}

.app-banner {
    background: linear-gradient(135deg, #0D3D14 0%, #1B5E20 50%, #2E7D32 100%);
    padding: 1.6rem 2.5rem; margin-bottom: 1.8rem; border-radius: 12px;
    display: flex; align-items: center; gap: 1.2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.app-banner h1 { color:#fff; font-weight:800; font-size:1.9rem; margin:0; letter-spacing:-0.5px; }
.app-banner p  { color:rgba(255,255,255,0.72); font-size:0.95rem; margin:0.2rem 0 0 0; }

.section-title {
    font-size:1.2rem; font-weight:700; color:#1B5E20;
    border-left:5px solid #1B5E20; padding-left:0.8rem; margin:1.5rem 0 1rem 0;
}
.kpi-card {
    background:white; border-radius:14px; padding:1.3rem 1.5rem;
    box-shadow:0 2px 12px rgba(0,0,0,0.06); border-top:5px solid #1B5E20;
}
.kpi-card.danger  { border-top-color:#C62828; }
.kpi-card.warning { border-top-color:#E65100; }
.kpi-card.info    { border-top-color:#1565C0; }
.kpi-label { font-size:0.73rem; font-weight:600; text-transform:uppercase; letter-spacing:0.8px; color:#78909C; margin-bottom:0.4rem; }
.kpi-value { font-size:1.8rem; font-weight:800; color:#1B2A1C; line-height:1.1; }
.kpi-value.danger  { color:#C62828; }
.kpi-value.warning { color:#E65100; }
.kpi-value.info    { color:#1565C0; }
.kpi-sub { font-size:0.73rem; color:#90A4AE; margin-top:0.3rem; }

.feature-card {
    background:white; border-radius:14px 14px 0 0; padding:1.6rem 1.6rem 1.2rem;
    box-shadow:0 2px 12px rgba(0,0,0,0.06); border:1px solid #E8F5E9; border-bottom:none;
}
.feature-card h3 { color:#0D3D14; font-weight:700; margin-top:0; }
.feature-card p  { color:#546E7A; line-height:1.6; margin:0; }
.feature-icon { font-size:2rem; margin-bottom:0.5rem; }

.step-row { display:flex; gap:0.8rem; margin-bottom:1.5rem; flex-wrap:wrap; }
.step-badge {
    background:white; border-radius:10px; padding:0.9rem 1rem;
    box-shadow:0 2px 8px rgba(0,0,0,0.06); flex:1; min-width:140px;
    display:flex; align-items:flex-start; gap:0.7rem;
}
.step-num {
    background:#1B5E20; color:white; border-radius:50%;
    width:25px; height:25px; display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:0.78rem; flex-shrink:0;
}
.step-text { font-size:0.78rem; color:#37474F; line-height:1.4; }
.step-text strong { color:#1B2A1C; display:block; margin-bottom:2px; }

.status-ok   { background:#E8F5E9; color:#1B5E20; padding:0.28rem 0.75rem; border-radius:20px; font-size:0.76rem; font-weight:600; display:inline-block; }
.status-warn { background:#FFF3E0; color:#E65100; padding:0.28rem 0.75rem; border-radius:20px; font-size:0.76rem; font-weight:600; display:inline-block; }

.upload-card {
    background:white; border-radius:14px; padding:1.3rem 1.5rem;
    box-shadow:0 2px 10px rgba(0,0,0,0.06); border:1px solid #E8F5E9; margin-bottom:0.6rem;
}
.upload-card-title { font-size:1rem; font-weight:700; color:#0D3D14; margin-bottom:0.3rem; }
.upload-card-desc  { font-size:0.8rem; color:#78909C; margin-bottom:0.7rem; line-height:1.5; }
.upload-col-tag {
    display:inline-block; background:#F1F8E9; color:#33691E;
    border:1px solid #C5E1A5; border-radius:5px;
    font-size:0.68rem; font-weight:600; padding:0.12rem 0.45rem; margin:2px; font-family:monospace;
}
.pill { display:inline-block; padding:0.18rem 0.6rem; border-radius:12px; font-size:0.72rem; font-weight:600; background:#FCE4D6; color:#BF360C; margin:2px; }
.pill.green { background:#E8F5E9; color:#1B5E20; }

.partner-card {
    background:white; border-radius:14px; padding:1.2rem 1.5rem;
    box-shadow:0 2px 10px rgba(0,0,0,0.06); border-left:6px solid #1B5E20; margin-bottom:0.9rem;
}
.partner-card.bad { border-left-color:#C62828; }
.partner-card.mid { border-left-color:#E65100; }
.partner-name  { font-size:1.05rem; font-weight:800; color:#1B2A1C; }
.partner-stats { display:flex; gap:1.8rem; flex-wrap:wrap; margin-top:0.6rem; }
.partner-stat-val { font-size:1.15rem; font-weight:800; color:#1B2A1C; }
.partner-stat-val.red { color:#C62828; }
.partner-stat-lbl { font-size:0.68rem; color:#78909C; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; }

[data-testid="stFileUploader"] {
    background:#FAFAFA; border:2px dashed #B0BEC5; border-radius:10px; padding:0.8rem;
}
.stButton > button[kind="primary"] {
    background:#1B5E20 !important; color:white !important;
    border-radius:8px !important; font-weight:600 !important;
    padding:0.65rem 1rem !important; border:none !important;
    box-shadow:0 2px 10px rgba(27,94,32,0.22) !important;
    transition:all 0.2s ease !important; width:100% !important; min-height:44px !important;
}
.stButton > button[kind="primary"]:hover {
    background:#2E7D32 !important; box-shadow:0 4px 16px rgba(27,94,32,0.32) !important;
    transform:translateY(-1px) !important;
}
.element-container:has(.feature-card) { margin-bottom:0 !important; }
[data-testid="column"] > div > div > div > div > .stButton > button[kind="primary"] {
    border-radius:0 0 14px 14px !important; margin-top:-1px !important;
}
.slim-divider { border:none; border-top:1px solid #E0E7EF; margin:1.2rem 0; }
.info-box {
    background:#E8F5E9; border-radius:10px; padding:0.9rem 1.2rem;
    border-left:4px solid #2E7D32; margin-bottom:1rem; color:#1B2A1C; font-size:0.87rem;
}
.warn-box {
    background:#FFF8E1; border-radius:10px; padding:0.9rem 1.2rem;
    border-left:4px solid #F9A825; margin-bottom:1rem; color:#3E2723; font-size:0.87rem;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar — always rendered, always visible ─────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1.2rem 0.5rem 0.8rem; text-align:center;
                border-bottom:1px solid rgba(255,255,255,0.12); margin-bottom:0.8rem;'>
        <div style='font-size:1.5rem;'>🌿</div>
        <div style='font-weight:900; font-size:1rem; color:white; margin-top:0.2rem;'>Mosaic Wellness</div>
        <div style='font-size:0.68rem; color:rgba(255,255,255,0.45); letter-spacing:1.5px;
                    text-transform:uppercase; margin-top:0.1rem;'>LogiAudit</div>
    </div>
    """, unsafe_allow_html=True)

    # Hide nav buttons during intro so sidebar just shows the brand
    if st.session_state["intro_seen"]:
        for icon, page, label in [
            ("🏠", "Home",     "Dashboard"),
            ("⚙️", "Admin",    "Admin Setup"),
            ("📝", "Employee", "Run Audit"),
            ("📊", "Results",  "Results"),
            ("🕰️", "History",  "History"),
        ]:
            if st.button(f"{icon}  {label}", key=f"nav_{page}", use_container_width=True):
                navigate_to(page)
                st.rerun()

        st.markdown("<div style='margin-top:0.8rem;'></div>", unsafe_allow_html=True)
        if st.session_state["inventory_master"] is not None:
            n = len(st.session_state["inventory_master"])
            st.markdown(f'<div class="status-ok" style="width:100%;box-sizing:border-box;margin-bottom:0.4rem;">✅ Inventory · {n} shipments</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-warn" style="width:100%;box-sizing:border-box;margin-bottom:0.4rem;">⚠️ No Inventory Loaded</div>', unsafe_allow_html=True)
        if st.session_state["audit_results"] is not None:
            st.markdown('<div class="status-ok" style="width:100%;box-sizing:border-box;margin-bottom:0.4rem;">✅ Audit Results Ready</div>', unsafe_allow_html=True)
        runs = len(st.session_state["audit_history"])
        if runs:
            st.markdown(f'<div style="font-size:0.7rem;color:rgba(255,255,255,0.38);margin-top:0.5rem;text-align:center;">{runs} audit run{"s" if runs>1 else ""} this session</div>', unsafe_allow_html=True)
    else:
        # During intro: just a clean brand tagline in the sidebar
        st.markdown("""
        <div style='padding:1rem 0.5rem; text-align:center;'>
            <div style='font-size:0.75rem; color:rgba(255,255,255,0.35); letter-spacing:2px;
                        text-transform:uppercase; line-height:2;'>
                Logistics Billing<br>Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_banner(icon, title, subtitle):
    st.markdown(f"""
    <div class="app-banner">
        <div style="font-size:2.1rem;">{icon}</div>
        <div><h1>{title}</h1><p>{subtitle}</p></div>
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# INTRO — fills the main content area, sidebar stays green alongside it
# Uses time.sleep so it auto-advances with zero JS, zero CSS hiding
# ════════════════════════════════════════════════════════════════════════
if not st.session_state["intro_seen"]:
    st.markdown("""
    <style>
    /* Full seamless green from top to bottom — header already hidden globally */
    [data-testid="stAppViewContainer"]      { background: linear-gradient(175deg, #0A2E0F 0%, #1B5E20 60%, #2E7D32 100%) !important; }
    [data-testid="stAppViewBlockContainer"] { background: transparent !important; padding: 0 !important; margin: 0 !important; }
    [data-testid="stMain"]                  { background: transparent !important; padding: 0 !important; margin: 0 !important; }
    [data-testid="stMainBlockContainer"]    { background: transparent !important; padding: 0 !important; margin: 0 !important; }
    .main                                   { background: transparent !important; padding: 0 !important; }
    .block-container                        { background: transparent !important; padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
    [data-testid="stVerticalBlock"]         { gap: 0 !important; padding: 0 !important; background: transparent !important; }
    .element-container                      { background: transparent !important; margin: 0 !important; padding: 0 !important; }
    html, body                              { background: #0A2E0F !important; margin: 0 !important; padding: 0 !important; }
    </style>

    <div style="text-align:center; padding: 4rem 2rem;">
        <div style="font-size: clamp(2.8rem, 5vw, 4.5rem); font-weight:900; color:#ffffff;
                    letter-spacing:-2px; line-height:1; margin-bottom:1rem;">
            Mosaic Wellness
        </div>
        <div style="font-size:1rem; color:rgba(255,255,255,0.55); letter-spacing:4px;
                    text-transform:uppercase; margin-bottom:0.5rem;">
            Logistics Billing Intelligence
        </div>
        <div style="font-size:0.75rem; color:rgba(255,255,255,0.28); letter-spacing:1px; margin-bottom:3rem;">
            Powered by LogiAudit &nbsp;·&nbsp; Internal Tool
        </div>
        <div style="width:140px; height:3px; background:rgba(255,255,255,0.15);
                    border-radius:99px; margin:0 auto; overflow:hidden;">
            <div style="height:100%; width:100%; background:rgba(255,255,255,0.55);
                        border-radius:99px;
                        animation: pulse 1.5s ease-in-out infinite alternate;">
            </div>
        </div>
        <style>
            @keyframes pulse { from { opacity:0.3; } to { opacity:1; } }
        </style>
    </div>
    """, unsafe_allow_html=True)

    time.sleep(3)
    st.session_state["intro_seen"] = True
    st.rerun()

    st.stop()


# ════════════════════════════════════════════════════════════════════════
# HOME
# ════════════════════════════════════════════════════════════════════════
elif st.session_state["current_page"] == "Home":
    render_banner("🌿", "Logistics Billing Checker",
                  "Mosaic Wellness · Deterministic audit engine · Zero AI hallucinations · Reconcile in minutes")

    st.markdown("""
    <div class="step-row">
        <div class="step-badge"><div class="step-num">1</div><div class="step-text"><strong>Admin — Upload Inventory</strong>Master shipment list with quantities, pincodes &amp; payment types.</div></div>
        <div class="step-badge"><div class="step-num">2</div><div class="step-text"><strong>Employee — Upload Contract</strong>The rate card agreed with each logistics partner.</div></div>
        <div class="step-badge"><div class="step-num">3</div><div class="step-text"><strong>Employee — Upload Invoice</strong>Monthly bill submitted by the courier.</div></div>
        <div class="step-badge"><div class="step-num">4</div><div class="step-text"><strong>Run Audit</strong>Engine flags overcharges, zone mismatches &amp; more.</div></div>
        <div class="step-badge"><div class="step-num">5</div><div class="step-text"><strong>Download Reports</strong>Export clean payout file &amp; discrepancy report.</div></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=False):
            st.markdown("""<div class="feature-card"><div class="feature-icon">⚙️</div><h3>Admin Portal</h3>
            <p>Upload and process the master inventory. Auto-calculates true shipment weights from SKU quantities and derives zones from pincode logic.</p></div>""", unsafe_allow_html=True)
            if st.button("Enter Admin Portal →", type="primary", key="home_admin", use_container_width=True):
                navigate_to("Admin"); st.rerun()
    with col2:
        with st.container(border=False):
            st.markdown("""<div class="feature-card"><div class="feature-icon">📝</div><h3>Employee Portal</h3>
            <p>Upload the partner contract and monthly invoice. Runs 8 deterministic checks against inventory ground truth and contract rates.</p></div>""", unsafe_allow_html=True)
            if st.button("Enter Employee Portal →", type="primary", key="home_emp", use_container_width=True):
                navigate_to("Employee"); st.rerun()
    with col3:
        with st.container(border=False):
            st.markdown("""<div class="feature-card"><div class="feature-icon">🔍</div><h3>What We Catch</h3>
            <p><span class="pill">Weight Overcharges</span><span class="pill">Zone Mismatches</span>
            <span class="pill">Invalid COD Fees</span><span class="pill">Invalid RTO Charges</span>
            <span class="pill">Duplicate AWBs</span><span class="pill">Ghost Shipments</span>
            <span class="pill">Rate Deviations</span><span class="pill">Uncontracted Surcharges</span></p></div>""", unsafe_allow_html=True)
            if st.session_state["audit_results"]:
                if st.button("View Latest Results →", type="primary", key="home_results", use_container_width=True):
                    navigate_to("Results"); st.rerun()
            else:
                st.button("No Results Yet", type="primary", key="home_results_dis", use_container_width=True, disabled=True)


# ════════════════════════════════════════════════════════════════════════
# ADMIN
# ════════════════════════════════════════════════════════════════════════
elif st.session_state["current_page"] == "Admin":
    render_banner("⚙️", "Admin Setup", "Upload the Internal Source of Truth · Processed once, used for every audit")

    st.markdown('<div class="section-title">Upload Master Inventory</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="upload-card">
        <div class="upload-card-title">📦 Inventory Master File</div>
        <div class="upload-card-desc">Your company's ground truth — one row per shipment. Used to validate every line in the courier invoice.</div>
        <strong style="font-size:0.74rem;color:#546E7A;">Required columns:</strong><br>
        <span class="upload-col-tag">AWB</span><span class="upload-col-tag">Delivery_Partner</span>
        <span class="upload-col-tag">Origin_Pincode</span><span class="upload-col-tag">Dest_Pincode</span>
        <span class="upload-col-tag">Qty_A</span><span class="upload-col-tag">Qty_B</span><span class="upload-col-tag">Qty_C</span>
        <span class="upload-col-tag">Payment_Type</span><span class="upload-col-tag">Delivery_Status</span>
        <div style="margin-top:0.55rem;font-size:0.73rem;color:#90A4AE;">Accepts <strong>.xlsx</strong> or <strong>.csv</strong></div>
    </div>
    """, unsafe_allow_html=True)

    inventory_file = st.file_uploader("Drop your Inventory Master file here (.xlsx or .csv)",
        type=["xlsx","csv"], help="One row per shipment.")

    if inventory_file:
        with st.spinner("Processing inventory — calculating weights & zones..."):
            try:
                raw_df    = pd.read_csv(inventory_file) if inventory_file.name.endswith('.csv') else pd.read_excel(inventory_file)
                processed = audit_engine.normalise_inventory(raw_df)
                st.session_state["inventory_master"] = processed
                total    = len(processed)
                partners = processed['Delivery_Partner'].nunique() if 'Delivery_Partner' in processed.columns else "—"
                zones    = processed['Calculated_Zone'].value_counts() if 'Calculated_Zone' in processed.columns else {}
                c1,c2,c3,c4 = st.columns(4)
                c1.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Shipments</div><div class="kpi-value">{total:,}</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Partners</div><div class="kpi-value">{partners}</div></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="kpi-card info"><div class="kpi-label">Local Zone A</div><div class="kpi-value info">{zones.get("Zone A (Local)",0)}</div></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="kpi-card info"><div class="kpi-label">National Zone D</div><div class="kpi-value info">{zones.get("Zone D (National)",0)}</div></div>', unsafe_allow_html=True)
                st.success(f"✅ Inventory processed — {total} shipments loaded.")
                with st.expander("🔍 Preview Processed Inventory (first 20 rows)"):
                    disp = [c for c in ['AWB','Delivery_Partner','Origin_Pincode','Dest_Pincode',
                                        'Qty_A','Qty_B','Qty_C','Calculated_Total_Weight_g',
                                        'Calculated_Zone','Payment_Type','Delivery_Status'] if c in processed.columns]
                    st.dataframe(processed[disp].head(20), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error: {e}")
    elif st.session_state["inventory_master"] is not None:
        n = len(st.session_state["inventory_master"])
        st.markdown(f'<div class="info-box">✅ Inventory already loaded: <strong>{n} shipments</strong>. Upload a new file above to replace it.</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# EMPLOYEE
# ════════════════════════════════════════════════════════════════════════
elif st.session_state["current_page"] == "Employee":
    render_banner("📝", "Run Audit", "Upload the Contract & Invoice · Deterministic reconciliation in seconds")

    if st.session_state["inventory_master"] is None:
        st.markdown('<div class="warn-box">🚨 <strong>Inventory not loaded.</strong> Ask the Admin to upload the master inventory first.</div>', unsafe_allow_html=True)
        if st.button("Go to Admin Portal →", type="primary", use_container_width=False):
            navigate_to("Admin"); st.rerun()
        st.stop()

    n_inv = len(st.session_state["inventory_master"])
    st.markdown(f'<div class="info-box">✅ Inventory loaded · <strong>{n_inv} shipments</strong>. Upload the rate contract and the invoice below to run the audit.</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Upload Audit Files</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("""
        <div class="upload-card">
            <div class="upload-card-title">📄 ① Rate Contract / Rate Card</div>
            <div class="upload-card-desc">The agreed pricing schedule between Mosaic Wellness and the delivery partner.</div>
            <strong style="font-size:0.73rem;color:#546E7A;">Required columns:</strong><br>
            <span class="upload-col-tag">Delivery_Partner</span><span class="upload-col-tag">Zone</span>
            <span class="upload-col-tag">Weight_Min_g</span><span class="upload-col-tag">Weight_Max_g</span>
            <span class="upload-col-tag">Base_Rate_Rs</span><span class="upload-col-tag">COD_Fee_Rs</span>
            <span class="upload-col-tag">RTO_Percentage</span>
        </div>""", unsafe_allow_html=True)
        contract_file = st.file_uploader("Drop the Rate Contract file here (.xlsx or .csv)",
            type=["xlsx","csv"], key="contract_up", help="Partner rate card.")
        if contract_file:
            st.success(f"✅ Contract loaded: **{contract_file.name}**")

    with col2:
        st.markdown("""
        <div class="upload-card">
            <div class="upload-card-title">🧾 ② Logistics Invoice</div>
            <div class="upload-card-desc">The monthly bill submitted by the courier. Cross-checked against contract rates and inventory.</div>
            <strong style="font-size:0.73rem;color:#546E7A;">Required columns:</strong><br>
            <span class="upload-col-tag">Tracking No</span><span class="upload-col-tag">Billed_Weight_g</span>
            <span class="upload-col-tag">Billed_Zone</span><span class="upload-col-tag">Base_Freight_Rs</span>
            <span class="upload-col-tag">COD_Charge_Rs</span><span class="upload-col-tag">RTO_Charge_Rs</span>
            <span class="upload-col-tag">Misc_Surcharge_Rs</span><span class="upload-col-tag">Total_Amount</span>
        </div>""", unsafe_allow_html=True)
        invoice_file = st.file_uploader("Drop the Logistics Invoice file here (.xlsx or .csv)",
            type=["xlsx","csv"], key="invoice_up", help="Courier invoice.")
        if invoice_file:
            st.success(f"✅ Invoice loaded: **{invoice_file.name}**")

    st.markdown("<hr class='slim-divider'>", unsafe_allow_html=True)

    if contract_file and invoice_file:
        st.markdown("""<div class="info-box">🔍 <strong>Checks that will run:</strong> Weight slab validation · Zone classification
            · COD eligibility · RTO eligibility · Duplicate AWB detection · Ghost shipment detection
            · Rate card compliance · Uncontracted surcharges</div>""", unsafe_allow_html=True)

        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            run_clicked = st.button("🚀 Run Automated Audit", type="primary", use_container_width=True)

        if run_clicked:
            with st.spinner("Running deterministic reconciliation engine..."):
                try:
                    raw_contract   = pd.read_csv(contract_file) if contract_file.name.endswith('.csv') else pd.read_excel(contract_file)
                    raw_invoice    = pd.read_csv(invoice_file)  if invoice_file.name.endswith('.csv')  else pd.read_excel(invoice_file)
                    clean_contract = audit_engine.normalise_contract(raw_contract)
                    clean_invoice  = audit_engine.normalise_invoice(raw_invoice)
                    results        = audit_engine.run_audit(st.session_state["inventory_master"], clean_contract, clean_invoice)
                    st.session_state["audit_results"] = results

                    s = results["summary"]
                    run_record = {
                        "Run Date":            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Invoice File":        invoice_file.name,
                        "Contract File":       contract_file.name,
                        "Total Billed (₹)":    round(s["total_billed"],      2),
                        "Approved Payout (₹)": round(s["approved_payout"],   2),
                        "Discrepancy (₹)":     round(s["total_discrepancy"], 2),
                        "Issues Found":        s["discrepancy_count"],
                    }
                    st.session_state["audit_history"].append(run_record)

                    full_data = results["full_data"]
                    disc_data = results["discrepancies"]
                    ph        = st.session_state["partner_history"]
                    if "Delivery_Partner" in full_data.columns:
                        inv_partner_map = (
                            st.session_state["inventory_master"][["AWB","Delivery_Partner"]]
                            .drop_duplicates(subset="AWB")
                        )
                        raw_inv_with_partner = clean_invoice.merge(inv_partner_map, on="AWB", how="left")
                        current_partner = clean_contract["Delivery_Partner"].iloc[0] if not clean_contract.empty else "Unknown"
                        raw_inv_with_partner["Delivery_Partner"] = raw_inv_with_partner["Delivery_Partner"].fillna(current_partner)
                        for partner, grp_raw in raw_inv_with_partner.groupby("Delivery_Partner"):
                            raw_billed = grp_raw["Total_Billed"].sum()
                            grp_fd     = full_data[full_data["Delivery_Partner"] == partner]
                            approved   = grp_fd["Expected_Total"].sum()
                            disc_grp   = disc_data[disc_data["AWB"].isin(grp_raw["AWB"])] if not disc_data.empty else pd.DataFrame()
                            ph.setdefault(partner, []).append({
                                "Run Date":            run_record["Run Date"],
                                "Invoice File":        invoice_file.name,
                                "Shipments":           len(grp_raw),
                                "Total Billed (₹)":    round(raw_billed, 2),
                                "Approved Payout (₹)": round(approved,   2),
                                "Discrepancy (₹)":     round(raw_billed - approved, 2),
                                "Issues Found":        len(disc_grp),
                            })

                    navigate_to("Results"); st.rerun()
                except Exception as e:
                    st.error(f"❌ Audit failed — please verify file formats. Error: {e}")
                    st.exception(e)
    else:
        st.markdown('<div style="color:#90A4AE;font-size:0.85rem;text-align:center;padding:0.8rem;">Upload both files above to enable the audit.</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# RESULTS
# ════════════════════════════════════════════════════════════════════════
elif st.session_state["current_page"] == "Results":
    render_banner("📊", "Audit Results", "Discrepancy breakdown · Download approved payout")

    if st.session_state["audit_results"] is None:
        st.markdown('<div class="warn-box">⚠️ No results yet. Run an audit first in the Employee Portal.</div>', unsafe_allow_html=True)
        if st.button("Go to Employee Portal →", type="primary", use_container_width=False):
            navigate_to("Employee"); st.rerun()
        st.stop()

    res    = st.session_state["audit_results"]
    s      = res["summary"]
    disc   = res["discrepancies"]
    payout = res["payout"]

    total_billed    = s["total_billed"]
    approved_payout = s["approved_payout"]
    total_disc      = s["total_discrepancy"]
    disc_count      = s["discrepancy_count"]
    savings_pct     = (total_disc / total_billed * 100) if total_billed else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Billed (Invoice)</div><div class="kpi-value">₹{total_billed:,.2f}</div><div class="kpi-sub">As submitted by courier</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Approved Payout</div><div class="kpi-value">₹{approved_payout:,.2f}</div><div class="kpi-sub">Per contract · unique shipments</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card danger"><div class="kpi-label">Overcharges Caught</div><div class="kpi-value danger">₹{total_disc:,.2f}</div><div class="kpi-sub">{savings_pct:.1f}% of invoice</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card warning"><div class="kpi-label">Discrepancy Count</div><div class="kpi-value warning">{disc_count}</div><div class="kpi-sub">Shipments with issues</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not disc.empty:
        st.markdown('<div class="section-title">Breakdown by Discrepancy Type</div>', unsafe_allow_html=True)
        type_summary = (disc.groupby("Discrepancy_Type")
            .agg(Count=("AWB","count"), Overcharge=("Diff_Total","sum"))
            .reset_index().sort_values("Overcharge", ascending=False))
        cols = st.columns(min(len(type_summary), 3))
        for i, (_, row) in enumerate(type_summary.iterrows()):
            colour = "#C62828" if row["Overcharge"] > 0 else "#1B5E20"
            sign   = "+" if row["Overcharge"] >= 0 else ""
            with cols[i % 3]:
                st.markdown(f"""<div style="background:white;border-radius:10px;padding:0.85rem 1rem;
                margin-bottom:0.7rem;box-shadow:0 1px 6px rgba(0,0,0,0.06);border-left:4px solid {colour};">
                <div style="font-size:0.7rem;font-weight:600;color:#78909C;text-transform:uppercase;margin-bottom:0.25rem;">{int(row['Count'])} shipment{"s" if row['Count']>1 else ""}</div>
                <div style="font-size:0.8rem;font-weight:600;color:#1B2A1C;margin-bottom:0.35rem;">{row['Discrepancy_Type']}</div>
                <div style="font-size:1.05rem;font-weight:800;color:{colour};">{sign}₹{row['Overcharge']:,.2f}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='slim-divider'>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🚨  Discrepancy Report", "✅  Clean Payout File"])

    with tab1:
        st.markdown(f"**{len(disc)} flagged shipments** — review before approving payment.")
        if not disc.empty:
            def style_diff(val):
                if isinstance(val, (int, float)):
                    if val > 0:   return "color: #C62828; font-weight: 700;"
                    elif val < 0: return "color: #1B5E20; font-weight: 700;"
                return ""
            st.dataframe(disc.style.applymap(style_diff, subset=["Diff_Total"]),
                         use_container_width=True, height=400)
        buf1 = BytesIO(); disc.to_excel(buf1, index=False)
        st.download_button("⬇️ Download Discrepancy Report (.xlsx)", data=buf1.getvalue(),
            file_name=f"discrepancy_report_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tab2:
        payout_display = payout[["AWB","Approved_Payout_Rs","Expected_Freight",
                                  "Expected_COD","Expected_RTO","Discrepancy_Type"]].copy()
        st.markdown(f"**{len(payout_display)} shipments approved** for payment.")
        st.dataframe(payout_display, use_container_width=True, height=400)
        buf2 = BytesIO(); payout.to_excel(buf2, index=False)
        st.download_button("⬇️ Download Approved Payout (.xlsx)", data=buf2.getvalue(),
            file_name=f"approved_payout_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ════════════════════════════════════════════════════════════════════════
# HISTORY
# ════════════════════════════════════════════════════════════════════════
elif st.session_state["current_page"] == "History":
    render_banner("🕰️", "Audit History", "Session log · Overall summary · Per-partner breakdown")

    history         = st.session_state["audit_history"]
    partner_history = st.session_state["partner_history"]

    if not history:
        st.markdown('<div class="warn-box">📭 No audits run yet this session. Head to the Employee Portal to get started.</div>', unsafe_allow_html=True)
        if st.button("Run First Audit →", type="primary", use_container_width=False):
            navigate_to("Employee"); st.rerun()
        st.stop()

    total_saved    = sum(h["Discrepancy (₹)"]  for h in history)
    total_billed_h = sum(h["Total Billed (₹)"] for h in history)
    total_issues   = sum(h["Issues Found"]      for h in history)

    st.markdown('<div class="section-title">Overall Session Summary</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-label">Audits Run</div><div class="kpi-value">{len(history)}</div><div class="kpi-sub">This session</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Total Billed</div><div class="kpi-value">₹{total_billed_h:,.2f}</div><div class="kpi-sub">Across all runs</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card danger"><div class="kpi-label">Total Overcharges Found</div><div class="kpi-value danger">₹{total_saved:,.2f}</div><div class="kpi-sub">{(total_saved/total_billed_h*100) if total_billed_h else 0:.1f}% of all invoices</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card warning"><div class="kpi-label">Total Issues Flagged</div><div class="kpi-value warning">{total_issues}</div><div class="kpi-sub">Across all audits</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Audit Run Log</div>', unsafe_allow_html=True)
    history_df = pd.DataFrame(history)
    st.dataframe(history_df, use_container_width=True)
    buf = BytesIO(); history_df.to_excel(buf, index=False)
    st.download_button("⬇️ Download Session Log (.xlsx)", data=buf.getvalue(),
        file_name=f"audit_history_{datetime.date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if partner_history:
        st.markdown("<hr class='slim-divider'>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Delivery Partner Scorecard</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.83rem;color:#546E7A;margin-bottom:1rem;">Aggregated across all audit runs — identifies which partner generates the most billing issues.</div>', unsafe_allow_html=True)

        partner_agg = []
        for partner, runs in partner_history.items():
            agg_billed    = sum(r["Total Billed (₹)"]    for r in runs)
            agg_payout    = sum(r["Approved Payout (₹)"] for r in runs)
            agg_disc      = sum(r["Discrepancy (₹)"]     for r in runs)
            agg_issues    = sum(r["Issues Found"]         for r in runs)
            agg_shipments = sum(r.get("Shipments", 0)    for r in runs)
            disc_pct      = (agg_disc / agg_billed * 100) if agg_billed else 0
            partner_agg.append(dict(partner=partner, billed=agg_billed, payout=agg_payout,
                disc=agg_disc, issues=agg_issues, shipments=agg_shipments, disc_pct=disc_pct))
        partner_agg.sort(key=lambda x: x["disc"], reverse=True)

        for pa in partner_agg:
            dp  = pa["disc_pct"]
            cls = "bad" if dp > 5 else ("mid" if dp > 2 else "")
            pill = (
                '<span style="background:#FFEBEE;color:#C62828;border-radius:12px;padding:0.15rem 0.6rem;font-size:0.68rem;font-weight:700;">⚠ HIGH RISK</span>'  if dp > 5 else
                '<span style="background:#FFF3E0;color:#E65100;border-radius:12px;padding:0.15rem 0.6rem;font-size:0.68rem;font-weight:700;">MODERATE</span>'       if dp > 2 else
                '<span style="background:#E8F5E9;color:#1B5E20;border-radius:12px;padding:0.15rem 0.6rem;font-size:0.68rem;font-weight:700;">✓ CLEAN</span>'
            )
            rd = 'red' if pa['disc'] > 0 else ''
            rp = 'red' if dp > 2 else ''
            ri = 'red' if pa['issues'] > 0 else ''
            st.markdown(f"""
            <div class="partner-card {cls}">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.65rem;">
                    <div class="partner-name">🚚 {pa['partner']}</div>{pill}
                </div>
                <div class="partner-stats">
                    <div><div class="partner-stat-val">₹{pa['billed']:,.2f}</div><div class="partner-stat-lbl">Total Billed</div></div>
                    <div><div class="partner-stat-val">₹{pa['payout']:,.2f}</div><div class="partner-stat-lbl">Approved Payout</div></div>
                    <div><div class="partner-stat-val {rd}">₹{pa['disc']:,.2f}</div><div class="partner-stat-lbl">Overcharges</div></div>
                    <div><div class="partner-stat-val {rp}">{dp:.1f}%</div><div class="partner-stat-lbl">Error Rate</div></div>
                    <div><div class="partner-stat-val {ri}">{pa['issues']}</div><div class="partner-stat-lbl">Issues</div></div>
                    <div><div class="partner-stat-val">{pa['shipments']}</div><div class="partner-stat-lbl">Shipments</div></div>
                </div>
            </div>""", unsafe_allow_html=True)
            with st.expander(f"📋 Run-by-run detail for {pa['partner']}"):
                st.dataframe(pd.DataFrame(partner_history[pa["partner"]]), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        all_rows = [{"Partner": p, **r} for p, runs in partner_history.items() for r in runs]
        if all_rows:
            buf_p = BytesIO(); pd.DataFrame(all_rows).to_excel(buf_p, index=False)
            st.download_button("⬇️ Download Partner Breakdown (.xlsx)", data=buf_p.getvalue(),
                file_name=f"partner_breakdown_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")