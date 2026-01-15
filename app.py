"""
Mabe PaceSetter Calculator - Carbon footprint calculator for household appliances.

Features:
- Extract annual kWh from Excel workbooks
- Calculate CO₂ footprint across lifecycle phases
- Export results as CSV
"""

import re
import time
from typing import Dict, List, Optional

import altair as alt
import pandas as pd
import streamlit as st

from extraction_core import (
    extract_required_inputs,
    compute_kpis,
    load_workbook_sheets,
    detect_model_sheets,
    Provenance,
    REQUIRED_KEYS,
)


# ---------------------- Page Config ----------------------
st.set_page_config(
    page_title="Mabe PaceSetter Calculator",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------- Design System ----------------------
BG = "#051C2C"
ACCENT = "#00D4FF"
TEXT = "#FFFFFF"
TEXT_DIM = "rgba(255,255,255,0.7)"
TEXT_MUTED = "rgba(255,255,255,0.5)"
BORDER = "rgba(255,255,255,0.08)"
CARD = "rgba(255,255,255,0.03)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

.stApp {{ background-color: {BG}; }}
.main .block-container {{ background-color: {BG}; padding-top: 2rem; }}

h1 {{ font-family: 'Playfair Display', serif !important; color: {TEXT} !important; font-weight: 700 !important; }}
h2, h3, h4 {{ font-family: 'Inter', sans-serif !important; color: {TEXT} !important; font-weight: 600 !important; }}
p, span, label, .stMarkdown {{ font-family: 'Inter', sans-serif !important; color: {TEXT_DIM} !important; }}

.step-header {{ display: flex; align-items: center; gap: 12px; margin: 1.5rem 0 1rem 0; }}
.step-num {{ background: {ACCENT}; color: {BG}; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; }}
.step-title {{ font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 600; color: {TEXT}; }}

.input-label {{ font-family: 'Inter', sans-serif; font-size: 15px; font-weight: 600; color: {TEXT}; margin-bottom: 6px; display: flex; align-items: center; gap: 10px; }}
.badge-ok {{ background: rgba(0, 212, 255, 0.15); color: {ACCENT}; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
.badge-manual {{ background: rgba(255, 170, 0, 0.15); color: #FFAA00; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }}

[data-testid="stMetricValue"] {{ color: {TEXT} !important; font-family: 'Playfair Display', serif !important; font-size: 2rem !important; }}
[data-testid="stMetricLabel"] {{ color: {TEXT_MUTED} !important; font-family: 'Inter', sans-serif !important; text-transform: uppercase; font-size: 12px !important; }}

.stButton > button {{ background: {ACCENT} !important; color: {BG} !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; transition: all 0.3s ease !important; }}
.stButton > button:hover {{ background: #33DFFF !important; box-shadow: 0 0 25px rgba(0, 212, 255, 0.3) !important; transform: translateY(-2px) !important; }}

.stDownloadButton > button {{ background: {CARD} !important; color: {TEXT} !important; border: 1px solid {BORDER} !important; border-radius: 8px !important; font-weight: 600 !important; }}
.stDownloadButton > button:hover {{ border-color: {ACCENT} !important; color: {ACCENT} !important; }}

[data-testid="stFileUploader"] {{ background: {CARD}; border: 2px dashed {BORDER}; border-radius: 12px; padding: 1rem; }}
[data-testid="stFileUploader"]:hover {{ border-color: {ACCENT}; }}
[data-testid="stFileUploader"] button {{ background: #4a5568 !important; color: white !important; border: none !important; border-radius: 6px !important; }}
[data-testid="stFileUploader"] button:hover {{ background: #5a6578 !important; }}
[data-testid="stFileUploader"] section {{ color: {TEXT_DIM} !important; }}
[data-testid="stFileUploader"] small {{ color: {TEXT_MUTED} !important; }}

.stSelectbox > div > div {{ background: {CARD} !important; border: 1px solid {BORDER} !important; border-radius: 8px !important; color: {TEXT} !important; }}
.stSelectbox label {{ color: {TEXT_DIM} !important; }}
.stNumberInput > div > div > input {{ background: {CARD} !important; border: 1px solid {BORDER} !important; border-radius: 8px !important; color: {TEXT} !important; }}
.stNumberInput label {{ color: {TEXT_DIM} !important; }}
.stRadio > label {{ color: {TEXT_DIM} !important; }}

hr {{ border-color: {BORDER} !important; margin: 2rem 0 !important; }}

.info-box {{ background: {CARD}; border-left: 3px solid {ACCENT}; border-radius: 0 8px 8px 0; padding: 1rem; color: {TEXT_DIM}; }}
.info-box strong {{ color: {TEXT}; }}

.warning-box {{ background: rgba(255, 170, 0, 0.08); border: 1px solid rgba(255, 170, 0, 0.3); border-radius: 8px; padding: 0.75rem 1rem; color: #FFAA00; font-size: 13px; margin-bottom: 1rem; }}

.energy-bar {{ display: flex; width: 100%; border-radius: 6px; overflow: hidden; margin-top: 0.5rem; }}
.energy-seg {{ flex: 1; text-align: center; padding: 12px 0; font-weight: 700; font-size: 1.1rem; transition: all 0.3s ease; }}
.energy-seg.active {{ box-shadow: 0 0 20px rgba(0, 212, 255, 0.5); transform: scale(1.08); z-index: 10; }}
.energy-arrow {{ text-align: center; font-size: 1.5rem; margin-bottom: -8px; color: {TEXT}; }}

.footer {{ text-align: center; padding: 2rem 0 1rem 0; color: {TEXT_MUTED}; font-size: 13px; }}
.footer a {{ color: {ACCENT}; text-decoration: none; }}
</style>
""", unsafe_allow_html=True)


# ---------------------- Constants ----------------------
GRID_FACTORS = {"Mexico (~0.42)": 0.42, "EU-27 (~0.25)": 0.25, "USA (~0.40)": 0.40, "Renewables (~0.10)": 0.10}
LIFETIME_DEFAULTS = {"Cooking": 10, "Cooling": 12, "Washing": 10, "Drying": 12}
PRODUCT_TYPES = ["Cooking", "Cooling", "Washing", "Drying"]
KWH_DEFAULTS = {"Cooking": 95.0, "Cooling": 190.0, "Washing": 150.0, "Drying": 400.0}
FRIENDLY_NAMES = {
    "Transport_kgCO2e": ("🚚", "Transport CO₂"),
    "Materials_kgCO2e": ("📦", "Materials CO₂"),
    "Production_kgCO2e": ("🏭", "Production CO₂"),
    "Use_kWh_per_year": ("⚡", "Annual kWh")
}


# ---------------------- Helpers ----------------------
def step_header(num: int, title: str):
    st.markdown(f'<div class="step-header"><div class="step-num">{num}</div><div class="step-title">{title}</div></div>', unsafe_allow_html=True)


def get_presets(key: str, extracted: float, product_type: str) -> List[float]:
    """Get preset values for a given key."""
    if extracted > 0:
        return [round(extracted * 0.9, 1), round(extracted, 1), round(extracted * 1.1, 1)]
    presets = {
        "Transport_kgCO2e": [2.0, 5.0, 10.0],
        "Materials_kgCO2e": [50.0, 100.0, 150.0],
        "Production_kgCO2e": [15.0, 25.0, 40.0],
        "Use_kWh_per_year": [round(KWH_DEFAULTS.get(product_type, 180) * x, 0) for x in [0.85, 1.0, 1.15]]
    }
    return presets.get(key, [0.0, 0.0, 0.0])


def suggest_label(kwh: float, product_type: str = "Cooling") -> str:
    """
    Return EU energy label based on kWh and product type.
    Different product types have different efficiency thresholds.
    """
    # Product-specific energy bands (kWh/year thresholds for A-F, G is above F)
    bands_by_type = {
        "Cooking": [50, 70, 95, 120, 150, 180],      # Ovens use less
        "Cooling": [100, 150, 200, 250, 300, 350],   # Fridges ~150-300
        "Washing": [80, 110, 140, 170, 200, 240],    # Washers ~100-200
        "Drying": [200, 300, 400, 500, 600, 700],    # Dryers use most
    }
    bands = bands_by_type.get(product_type, [110, 140, 180, 220, 270, 330])
    for i, limit in enumerate(bands):
        if kwh <= limit:
            return "ABCDEFG"[i]
    return "G"


def to_csv(rows: List[List], delimiter: str = ",") -> bytes:
    """Convert rows to CSV bytes with BOM."""
    def esc(cell):
        s = str(cell)
        return f'"{s}"' if any(c in s for c in ["\n", delimiter, '"']) else s
    body = "\r\n".join([delimiter.join(esc(c) for c in row) for row in rows])
    return b"\xef\xbb\xbf" + body.encode("utf-8")


# ---------------------- App ----------------------
st.markdown("# 🌿 Mabe PaceSetter")
st.markdown("*Carbon footprint calculator for household appliances*")
st.divider()

# STEP 1: Upload
step_header(1, "Upload Data")
col1, col2 = st.columns([2, 1])
with col1:
    file = st.file_uploader("Drop your Excel workbook here", type=["xlsx", "xlsm", "xls"])
with col2:
    st.markdown('<div class="info-box"><strong>What we extract:</strong><br>• Annual kWh consumption<br>• Product specifications</div>', unsafe_allow_html=True)

dfs, wb_bytes = {}, None
if file:
    with st.spinner("Analyzing..."):
        wb_bytes = file.read()
        file.seek(0)
        dfs = load_workbook_sheets(wb_bytes)
    st.success(f"✓ Found **{len(dfs)} sheets**")


# STEP 2: Select Product
if dfs and wb_bytes:
    st.divider()
    step_header(2, "Select Product")
    
    col1, col2 = st.columns(2)
    with col1:
        product_type = st.selectbox("Category", PRODUCT_TYPES, index=3 if "Dryer" in str(list(dfs.keys())) else 1)
        st.session_state.product_type = product_type
    with col2:
        model_sheets = detect_model_sheets(list(dfs.keys()))
        sheet = st.selectbox("Data Sheet", list(dfs.keys()), index=list(dfs.keys()).index(model_sheets[0]) if model_sheets and model_sheets[0] in dfs else 0)
    
    extraction = extract_required_inputs(wb_bytes, sheet)
    
    # STEP 3: Review Inputs
    st.divider()
    step_header(3, "Review Inputs")
    
    # Show warning for failed extractions
    failed = [k for k, v in extraction.inputs.items() if v == 0 and k in REQUIRED_KEYS]
    if failed:
        st.markdown(f'<div class="warning-box">⚠️ Could not auto-extract: {", ".join(failed)}. Please enter manually.</div>', unsafe_allow_html=True)
    
    inputs = {}
    col1, col2 = st.columns(2)
    
    for i, key in enumerate(REQUIRED_KEYS):
        with (col1 if i % 2 == 0 else col2):
            extracted_val = extraction.inputs.get(key, 0.0)
            prov = extraction.provenance.get(key)
            icon, name = FRIENDLY_NAMES.get(key, ("📊", key))
            is_extracted = prov and prov.method in ("anchor", "table") and extracted_val > 0
            
            # Label with badge
            badge = f'<span class="badge-ok">Extracted: {extracted_val:.1f}</span>' if is_extracted else '<span class="badge-manual">Manual</span>'
            st.markdown(f'<div class="input-label">{icon} {name} {badge}</div>', unsafe_allow_html=True)
            
            # Presets and input
            presets = get_presets(key, extracted_val if is_extracted else 0, product_type)
            selected = st.radio("Presets", presets, horizontal=True, key=f"p_{key}", index=1 if is_extracted else 0, label_visibility="collapsed")
            inputs[key] = st.number_input("Value", value=float(selected), min_value=0.0, step=1.0 if "kWh" in key else 0.1, key=f"v_{key}", label_visibility="collapsed")
    
    st.session_state.inputs = inputs


# STEP 4: Calculate
if hasattr(st.session_state, "inputs"):
    st.divider()
    step_header(4, "Calculate")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        grid_choice = st.selectbox("Grid Factor", list(GRID_FACTORS.keys()))
        grid_factor = GRID_FACTORS[grid_choice]
    with col2:
        grid_factor = st.number_input("Custom (kg/kWh)", value=grid_factor, min_value=0.05, max_value=1.0, step=0.01)
    with col3:
        ptype = getattr(st.session_state, "product_type", "Cooling")
        lifetime = st.number_input("Lifetime (years)", value=LIFETIME_DEFAULTS.get(ptype, 10), min_value=1, max_value=30)
    
    if st.button("Calculate CO₂ Footprint", use_container_width=True):
        with st.spinner("Calculating..."):
            time.sleep(0.2)
            st.session_state.results = compute_kpis(st.session_state.inputs, grid_factor, lifetime)
            st.session_state.grid_factor = grid_factor
            st.session_state.lifetime = lifetime


# STEP 5: Results
if hasattr(st.session_state, "results"):
    st.divider()
    step_header(5, "Results")
    
    r = st.session_state.results
    kwh = st.session_state.inputs.get("Use_kWh_per_year", 0)
    ptype = getattr(st.session_state, "product_type", "Cooling")
    
    # Calculate energy label ONCE and store in session state
    st.session_state.energy_label = suggest_label(kwh, ptype)
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total CO₂", f"{r['Total_CO2e']:,.0f} kg")
    col2.metric("Use Phase", f"{r['UsePhase_CO2e']:,.0f} kg")
    col3.metric("Energy Label", st.session_state.energy_label)
    
    # Formula explanation
    st.caption(f"Use phase = {kwh:.0f} kWh/yr × {st.session_state.lifetime} yrs × {st.session_state.grid_factor:.2f} kg/kWh = {r['UsePhase_CO2e']:,.0f} kg")
    
    # Phase Breakdown - heading OUTSIDE columns with spacing
    st.markdown("#### Phase Breakdown")
    st.markdown("")  # Add spacing
    
    phase_data = pd.DataFrame({
        "Phase": ["Transport", "Materials", "Production", "Use Phase"],
        "Share": [r["Share_Transport_%"], r["Share_Materials_%"], r["Share_Production_%"], r["Share_Use_%"]]
    })
    
    donut = alt.Chart(phase_data).mark_arc(innerRadius=50, outerRadius=90).encode(
        theta=alt.Theta("Share:Q"),
        color=alt.Color("Phase:N", scale=alt.Scale(domain=["Transport", "Materials", "Production", "Use Phase"], range=["#17a2b8", "#6f42c1", "#fd7e14", ACCENT]), legend=None),
        tooltip=["Phase", alt.Tooltip("Share:Q", format=".1f", title="Share %")]
    ).properties(width=200, height=200).configure_view(strokeWidth=0).configure(background="transparent")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.altair_chart(donut, use_container_width=True)
    with col2:
        for phase, share_key, co2_key in [("🚚 Transport", "Share_Transport_%", "Transport_kgCO2e"), ("📦 Materials", "Share_Materials_%", "Materials_kgCO2e"), ("🏭 Production", "Share_Production_%", "Production_kgCO2e"), ("⚡ Use Phase", "Share_Use_%", "UsePhase_CO2e")]:
            st.markdown(f"**{phase}**: {r[co2_key]:,.0f} kg ({r[share_key]:.1f}%)")
    
    # Energy Efficiency - use session state for consistency
    st.markdown("#### Energy Efficiency")
    energy_label_for_arrow = st.session_state.energy_label
    idx = list("ABCDEFG").index(energy_label_for_arrow)
    arrow_pct = (idx + 0.5) / 7 * 100
    
    # Arrow and bar in same container so arrow is positioned RELATIVE to bar
    colors = ["#00A651", "#39B54A", "#8DC63F", "#FFEB3B", "#FFA726", "#F57C00", "#EF5350"]
    bar_html = f'''
    <div style="position: relative; width: 100%;">
        <div style="position: absolute; left: {arrow_pct}%; transform: translateX(-50%); top: -20px; font-size: 1.5rem; color: white;">↓</div>
        <div style="display: flex; width: 100%; border-radius: 6px; overflow: hidden;">
    '''
    for i, (c, lbl) in enumerate(zip(colors, "ABCDEFG")):
        active_style = "box-shadow: 0 0 20px rgba(0,212,255,0.5); transform: scale(1.08); z-index: 10;" if i == idx else ""
        tc = "#FFF" if i not in [3, 4] else "#333"
        bar_html += f'<div style="flex: 1; text-align: center; padding: 12px 0; font-weight: 700; font-size: 1.1rem; background: {c}; color: {tc}; {active_style}">{lbl}</div>'
    bar_html += '</div></div>'
    st.markdown(bar_html, unsafe_allow_html=True)


# STEP 6: Export
if hasattr(st.session_state, "results"):
    st.divider()
    step_header(6, "Export")
    
    r = st.session_state.results
    rows = [
        ["Mabe PaceSetter Results"], [""],
        ["Product Type", st.session_state.product_type],
        ["Energy Label", st.session_state.energy_label],
        ["Annual kWh", f"{st.session_state.inputs.get('Use_kWh_per_year', 0):.1f}"],
        ["Lifetime (years)", str(st.session_state.lifetime)],
        ["Grid Factor", f"{st.session_state.grid_factor:.2f}"],
        [""], ["Phase", "kg CO₂", "Share %"],
        ["Transport", f"{r['Transport_kgCO2e']:.1f}", f"{r['Share_Transport_%']:.1f}"],
        ["Materials", f"{r['Materials_kgCO2e']:.1f}", f"{r['Share_Materials_%']:.1f}"],
        ["Production", f"{r['Production_kgCO2e']:.1f}", f"{r['Share_Production_%']:.1f}"],
        ["Use Phase", f"{r['UsePhase_CO2e']:.1f}", f"{r['Share_Use_%']:.1f}"],
        ["TOTAL", f"{r['Total_CO2e']:.1f}", "100.0"],
    ]
    
    st.download_button("📥 Download CSV", to_csv(rows), file_name=f"pacesetter_{st.session_state.product_type.lower()}.csv", mime="text/csv", use_container_width=True)


# Footer
st.markdown("---")
st.markdown('<div class="footer">NEONEX · <a href="mailto:felix.schmidt@neonex.de">felix.schmidt@neonex.de</a></div>', unsafe_allow_html=True)
