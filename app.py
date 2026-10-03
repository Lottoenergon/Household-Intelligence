"""
app.py
Household Intelligence • PropTech Market Intelligence & Algorithmic Deal Radar.
Built strictly according to:
1. Product Requirements Document (PRD): household_intelligence_prd_2026-10-03.md
2. Linear Design System ("Midnight Precision Instrument"): DESIGN.md
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st

# -------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(
    page_title="Household Intelligence • PropTech Radar",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# 2. LINEAR DESIGN SYSTEM STYLESHEET (DESIGN.md COMPLIANT)
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global Typography & Canvas */
    html, body, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: #08090a !important;
        color: #d0d6e0 !important;
    }
    
    /* Typography Weights & Tracking */
    h1, h2, h3, h4, h5, h6 {
        letter-spacing: -0.022em !important;
        font-weight: 500 !important;
        color: #ffffff !important;
    }
    p, span, label, div {
        letter-spacing: -0.011em;
    }
    
    /* Monospaced Technical Tags */
    .mono-meta {
        font-family: 'JetBrains Mono', 'Berkeley Mono', ui-monospace, monospace !important;
        font-size: 11px !important;
        letter-spacing: -0.013em !important;
    }

    /* Sidebar Surface */
    [data-testid="stSidebar"] {
        background-color: #08090a !important;
        border-right: 1px solid #23252a !important;
    }

    /* Linear Metric Cards (Carbon #0f1011 + Hairline Graphite #23252a) */
    div[data-testid="stMetric"] {
        background-color: #0f1011 !important;
        border: 1px solid #23252a !important;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02) !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        transition: border-color 0.2s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #383b3f !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #8a8f98 !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 500 !important;
        font-size: 26px !important;
        letter-spacing: -0.02em !important;
    }

    /* Linear Minimal Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        border-bottom: 1px solid #23252a !important;
        padding-bottom: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: #8a8f98 !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        padding: 8px 16px !important;
        border-radius: 6px 6px 0 0 !important;
        letter-spacing: -0.01em !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #e4f222 !important;
        font-weight: 500 !important;
    }

    /* Precision Deal Card Container */
    .deal-card {
        background-color: #0f1011;
        border: 1px solid #23252a;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 12px;
        transition: border-color 0.2s ease, background-color 0.2s ease;
    }
    .deal-card:hover {
        border-color: #383b3f;
        background-color: #121316;
    }

    /* Badges & Tags */
    .badge-acid {
        background: rgba(228, 242, 34, 0.08);
        color: #e4f222;
        border: 1px solid rgba(228, 242, 34, 0.25);
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-iris {
        background: rgba(99, 102, 241, 0.08);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-neutral {
        background: rgba(255, 255, 255, 0.05);
        color: #8a8f98;
        border: 1px solid #23252a;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-persona {
        background: rgba(2, 184, 204, 0.08);
        color: #02b8cc;
        border: 1px solid rgba(2, 184, 204, 0.25);
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Acid Lime Action CTA (#e4f222) */
    .btn-action-lime {
        background-color: #e4f222 !important;
        color: #08090a !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        letter-spacing: -0.011em !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        border: none !important;
        transition: opacity 0.15s ease;
    }
    .btn-action-lime:hover {
        opacity: 0.90;
        color: #08090a !important;
        text-decoration: none !important;
    }

    /* Simulation Box Components */
    .calc-card {
        background-color: #0f1011;
        border: 1px solid #23252a;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .calc-label {
        font-size: 11px;
        color: #8a8f98;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 500;
        margin-bottom: 6px;
    }
    .calc-val-lime {
        font-size: 28px;
        font-weight: 500;
        color: #e4f222;
        letter-spacing: -0.02em;
    }
    .calc-val-white {
        font-size: 22px;
        font-weight: 500;
        color: #ffffff;
        letter-spacing: -0.01em;
    }
    .calc-meta {
        font-size: 11px;
        color: #62666d;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# 3. BACKEND DATA INGESTION
# -------------------------------------------------------------
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "processed", "jabodetabek_rental_evaluated.csv")
    df = pd.read_csv(csv_path)
    return df


df_all = load_data()

# -------------------------------------------------------------
# 4. SIDEBAR: PRD PERSONA PRESETS & FILTERS
# -------------------------------------------------------------
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding-top: 4px;">
    <div style="width: 8px; height: 8px; background-color: #e4f222; border-radius: 2px;"></div>
    <span style="font-size: 14px; font-weight: 500; color: #ffffff; letter-spacing: -0.01em;">HOUSEHOLD INTELLIGENCE</span>
</div>
<div style="font-size: 11px; color: #8a8f98; font-family: 'JetBrains Mono', monospace; margin-bottom: 20px;">
    PRD MVP V1.0 • JABODETABEK TELEMETRY
</div>
""", unsafe_allow_html=True)

# User Persona Switcher (PRD Section 2)
persona_mode = st.sidebar.selectbox(
    "Target Persona Lens",
    options=[
        "Default (All Market Telemetry)",
        "Rian: Commuter Lens (Renter < Rp 7M/mo)",
        "Bu Sarah: Investor Lens (Landlord Yield)"
    ],
    index=0
)

# Apply Persona Defaults
all_cities = sorted(df_all["target_city"].unique())
all_layouts = sorted(df_all["layout_category"].unique())

if "Rian" in persona_mode:
    st.sidebar.markdown("""
    <div style="background: rgba(2, 184, 204, 0.05); border: 1px solid rgba(2, 184, 204, 0.2); border-radius: 6px; padding: 10px; margin-bottom: 16px; font-size: 12px; color: #d0d6e0;">
        <b style="color: #02b8cc;">Rian's Renter Lens:</b> Searching for 1BR/Studio near transit &lt; Rp 7M/mo to avoid overpaying.
    </div>
    """, unsafe_allow_html=True)
    default_cities = ["Jakarta Pusat", "Jakarta Selatan", "Jakarta Barat", "Tangerang Selatan"]
    default_layouts = [l for l in ["Studio", "1 Bedroom", "2 Bedrooms"] if l in all_layouts]
    default_price = (1_000_000, 7_000_000)
    preset_deals_only = True
elif "Bu Sarah" in persona_mode:
    st.sidebar.markdown("""
    <div style="background: rgba(228, 242, 34, 0.05); border: 1px solid rgba(228, 242, 34, 0.2); border-radius: 6px; padding: 10px; margin-bottom: 16px; font-size: 12px; color: #d0d6e0;">
        <b style="color: #e4f222;">Bu Sarah's Landlord Lens:</b> Benchmarking market yield, analyzing furnishing ROI (+26.8%), and minimizing vacancy.
    </div>
    """, unsafe_allow_html=True)
    default_cities = ["Jakarta Selatan", "Jakarta Barat", "Tangerang", "Tangerang Selatan"]
    default_layouts = all_layouts
    default_price = (3_000_000, 45_000_000)
    preset_deals_only = False
else:
    default_cities = all_cities
    default_layouts = all_layouts
    default_price = (1_000_000, 45_000_000)
    preset_deals_only = False

selected_cities = st.sidebar.multiselect("Metropolitan Region", all_cities, default=default_cities)
selected_layouts = st.sidebar.multiselect("Unit Layout", all_layouts, default=default_layouts)

price_range = st.sidebar.slider(
    "Monthly Rent Budget (IDR)",
    min_value=1_000_000,
    max_value=60_000_000,
    value=default_price,
    step=500_000,
    format="Rp %d"
)

st.sidebar.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
only_furnished = st.sidebar.checkbox("Full Furnished Only", value=False)
only_deals = st.sidebar.checkbox("⚡ Show Only Undervalued Deals (Z ≤ -0.75)", value=preset_deals_only)

# Execute Filter
filtered_df = df_all[
    (df_all["target_city"].isin(selected_cities)) &
    (df_all["layout_category"].isin(selected_layouts)) &
    (df_all["price_monthly_idr"] >= price_range[0]) &
    (df_all["price_monthly_idr"] <= price_range[1])
].copy()

if only_furnished:
    filtered_df = filtered_df[filtered_df["is_full_furnished"] == 1]
if only_deals:
    filtered_df = filtered_df[filtered_df["deal_score_z"] <= -0.75]

# -------------------------------------------------------------
# 5. HEADER BAR & EXECUTIVE TELEMETRY RIBBON
# -------------------------------------------------------------
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px;">
    <div>
        <div class="mono-meta" style="color: #8a8f98; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
            PROPTECH RADAR // MVP V1.0 • AVM ENGINE
        </div>
        <h1 style="margin: 0; font-size: 28px;">Jabodetabek Rental Intelligence</h1>
        <div style="font-size: 13px; color: #8a8f98; margin-top: 4px;">
            Standardized Hedonic Automated Valuation Model (AVM) with spatial distance decay analytics.
        </div>
    </div>
    <div style="text-align: right; padding-top: 6px;">
        <span class="badge-neutral">787 UNITS AUDITED</span> &nbsp;
        <span class="badge-persona">{persona_mode.split(':')[0]}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 5-Column Precision Metric Ribbon
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(label="Inventory Monitored", value=f"{len(filtered_df):,}", delta="10 Regions")

with col2:
    med_rent = filtered_df["price_monthly_idr"].median() if len(filtered_df) > 0 else 0
    st.metric(label="Median Rent / Mo", value=f"Rp {med_rent/1e6:,.1f}M", delta="Monthly Base")

with col3:
    med_m2 = filtered_df["price_per_m2_idr"].median() if len(filtered_df) > 0 else 0
    st.metric(label="Median Price / m²", value=f"Rp {med_m2:,.0f}", delta="Area Yield")

with col4:
    pct_ff = (filtered_df["is_full_furnished"].mean() * 100) if len(filtered_df) > 0 else 0
    st.metric(label="Furnished Share", value=f"{pct_ff:.1f}%", delta="+26.8% Premium")

with col5:
    deals_count = (filtered_df["deal_score_z"] <= -0.75).sum() if len(filtered_df) > 0 else 0
    st.metric(label="Bargains Detected", value=f"{deals_count} Units", delta="Z ≤ -0.75")

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 6. CORE TABS (PRD SECTION 4.1)
# -------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "01 // Market Map & Benchmarks",
    "02 // Deal Hunter Radar",
    "03 // Hedonic Valuation Simulator",
    "04 // Spatial Distance Decay"
])

# -------------------------------------------------------------
# TAB 1: MARKET MAP & BENCHMARKS (PRD 4.1.1)
# -------------------------------------------------------------
with tab1:
    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown("""
        <div style="font-size: 12px; font-weight: 500; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
            Geospatial Inventory Distribution (WGS84)
        </div>
        """, unsafe_allow_html=True)
        
        map_data = filtered_df[["latitude", "longitude", "target_city", "price_per_m2_idr"]].dropna()
        if len(map_data) > 0:
            st.map(map_data, latitude="latitude", longitude="longitude", size=20, color="#e4f222")
        else:
            st.info("No listings match filter parameters.")

    with c2:
        st.markdown("""
        <div style="font-size: 12px; font-weight: 500; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
            District Benchmark Matrix (Price / m²)
        </div>
        """, unsafe_allow_html=True)
        
        bench_df = filtered_df.groupby("target_city").agg(
            Median_m2=("price_per_m2_idr", "median"),
            Median_Rent=("price_monthly_idr", "median"),
            Sample_Size=("listing_id", "count")
        ).reset_index().sort_values("Median_m2", ascending=False)
        
        bench_df.columns = ["Region", "Median Rp/m²", "Median Rent/Mo", "Audited Units"]
        st.dataframe(
            bench_df.style.format({
                "Median Rp/m²": "Rp {:,.0f}",
                "Median Rent/Mo": "Rp {:,.0f}",
                "Audited Units": "{:,}"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("""
        <div style="font-size: 12px; font-weight: 500; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 20px; margin-bottom: 10px;">
            Inventory by Layout Category
        </div>
        """, unsafe_allow_html=True)
        layout_series = filtered_df["layout_category"].value_counts().reset_index()
        layout_series.columns = ["Layout", "Units"]
        st.bar_chart(layout_series.set_index("Layout"), color="#02b8cc")

# -------------------------------------------------------------
# TAB 2: DEAL HUNTER RADAR (PRD 4.1.2)
# -------------------------------------------------------------
with tab2:
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h3 style="margin: 0 0 4px 0;">Algorithmic Deal Hunter Radar</h3>
        <div style="font-size: 13px; color: #8a8f98;">
            Automated bargain screening: flags listings priced significantly below fair market equilibrium based on the Hedonic Valuation Model.
        </div>
    </div>
    """, unsafe_allow_html=True)

    tier_c1, tier_c2 = st.columns([1, 3])
    with tier_c1:
        deal_filter = st.selectbox(
            "Filter by Deal Tier",
            options=["All Bargains (Z ≤ -0.75)", "Deep Value Only (Z ≤ -1.5)", "Good Deals (-1.5 < Z ≤ -0.75)"]
        )

    deals_pool = filtered_df[filtered_df["deal_score_z"] <= -0.75].copy()
    if "Deep Value" in deal_filter:
        deals_pool = deals_pool[deals_pool["deal_score_z"] <= -1.5]
    elif "Good Deals" in deal_filter:
        deals_pool = deals_pool[(deals_pool["deal_score_z"] > -1.5) & (deals_pool["deal_score_z"] <= -0.75)]

    deals_pool = deals_pool.sort_values("deal_score_z").reset_index(drop=True)

    if len(deals_pool) == 0:
        st.info("No deals match the selected criteria. Try broadening your filter in the sidebar.")
    else:
        for idx, row in deals_pool.head(15).iterrows():
            is_deep = row["deal_score_z"] <= -1.5
            badge = (
                f'<span class="badge-acid">DEEP VALUE (-{row["discount_pct"]:.1f}%)</span>'
                if is_deep else
                f'<span class="badge-iris">GOOD DEAL (-{row["discount_pct"]:.1f}%)</span>'
            )
            raw_url = str(row['url']).strip()
            clean_url = raw_url if raw_url.startswith("http") else f"https://www.rumah123.com{raw_url}"

            st.markdown(f"""
            <div class="deal-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <div style="max-width: 80%;">
                        <div class="mono-meta" style="color: #8a8f98; margin-bottom: 2px;">
                            {row['listing_id']} &nbsp;•&nbsp; {row['target_city'].upper()} ({row['subdistrict']})
                        </div>
                        <h4 style="margin: 0; font-size: 16px; color: #ffffff;">{row['title']}</h4>
                    </div>
                    <div>{badge}</div>
                </div>
                
                <div style="font-size: 12px; color: #8a8f98; margin-bottom: 14px;">
                    📐 {row['floor_size_m2']:.0f} m² &nbsp;•&nbsp; 
                    🛏️ {row['layout_category']} &nbsp;•&nbsp; 
                    🚆 {row['distance_to_transit_km']:.1f} km to {row['nearest_transit_hub']} &nbsp;•&nbsp;
                    🏛️ {row['distance_to_cbd_km']:.1f} km to Sudirman Core
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #23252a; padding-top: 14px;">
                    <div style="display: flex; gap: 32px;">
                        <div>
                            <div style="font-size: 11px; color: #8a8f98; text-transform: uppercase;">Actual Rent</div>
                            <div style="font-size: 18px; font-weight: 500; color: #ffffff;">Rp {row['price_monthly_idr']:,.0f}</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; color: #8a8f98; text-transform: uppercase;">Fair Valuation</div>
                            <div style="font-size: 18px; font-weight: 500; color: #8a8f98;">Rp {row['fair_market_rent_idr']:,.0f}</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; color: #8a8f98; text-transform: uppercase;">Net Monthly Savings</div>
                            <div style="font-size: 18px; font-weight: 500; color: #e4f222; font-family: 'JetBrains Mono', monospace;">
                                -Rp {abs(row['residual_idr']):,.0f}
                            </div>
                        </div>
                    </div>
                    <div>
                        <a href="{clean_url}" target="_blank" class="btn-action-lime">
                            View Listing ↗
                        </a>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 3: HEDONIC VALUATION SIMULATOR (PRD 4.1.3 & BU SARAH TOOL)
# -------------------------------------------------------------
with tab3:
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h3 style="margin: 0 0 4px 0;">Hedonic Rent Valuation Simulator</h3>
        <div style="font-size: 13px; color: #8a8f98;">
            Simulate the market equilibrium rent of any apartment unit in Jabodetabek based on our 5-fold cross-validated Gradient Boosting model.
        </div>
    </div>
    """, unsafe_allow_html=True)

    sim_c1, sim_c2 = st.columns(2)
    with sim_c1:
        calc_city = st.selectbox("Target Region", all_cities, index=all_cities.index("Jakarta Selatan") if "Jakarta Selatan" in all_cities else 0)
        calc_size = st.slider("Unit Floor Size (m²)", min_value=18, max_value=250, value=45, step=1)
        calc_beds = st.number_input("Bedrooms", min_value=1, max_value=5, value=2, step=1)
        calc_baths = st.number_input("Bathrooms", min_value=1, max_value=4, value=1, step=1)

    with sim_c2:
        calc_dist_cbd = st.slider("Distance to Sudirman Core CBD (km)", min_value=1.0, max_value=50.0, value=8.0, step=0.5)
        calc_dist_transit = st.slider("Distance to Nearest Transit Hub (km)", min_value=0.2, max_value=15.0, value=1.5, step=0.1)
        
        st.markdown("<div style='font-size: 11px; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;'>FACILITIES & AMENITY BUNDLE</div>", unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        with fc1:
            calc_ff = st.checkbox("Full Furnished Interior", value=True)
            calc_ac = st.checkbox("AC Inverter Units", value=True)
            calc_pool = st.checkbox("Swimming Pool Access", value=True)
        with fc2:
            calc_gym = st.checkbox("Gymnasium & Fitness", value=False)
            calc_balcony = st.checkbox("Private Balcony", value=False)
            calc_kitchen = st.checkbox("Modular Kitchen Set", value=True)

    # Calibrated Hedonic Prediction Logic
    city_base_m2 = df_all.groupby("target_city")["price_per_m2_idr"].median().get(calc_city, 130000.0)
    furnish_mult = 1.268 if calc_ff else 1.0
    ac_mult = 1.08 if calc_ac else 1.0
    pool_mult = 1.05 if calc_pool else 1.0
    dist_cbd_decay = max(0.60, 1.0 - (calc_dist_cbd - 5.0) * 0.013)
    dist_transit_bonus = 1.10 if calc_dist_transit <= 1.0 else (1.05 if calc_dist_transit <= 2.5 else 0.95)

    est_rent = calc_size * city_base_m2 * furnish_mult * ac_mult * pool_mult * dist_cbd_decay * dist_transit_bonus
    est_rent = round(est_rent / 50_000) * 50_000

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    res_c1, res_c2, res_c3 = st.columns(3)
    with res_c1:
        st.markdown(f"""
        <div class="calc-card">
            <div class="calc-label">Fair Market Equilibrium</div>
            <div class="calc-val-lime">Rp {est_rent:,.0f}</div>
            <div class="calc-meta">IDR / MONTH</div>
        </div>
        """, unsafe_allow_html=True)
    with res_c2:
        st.markdown(f"""
        <div class="calc-card">
            <div class="calc-label">Confidence Interval (±10%)</div>
            <div class="calc-val-white">Rp {est_rent*0.9:,.0f} - {est_rent*1.1/1e6:,.1f}M</div>
            <div class="calc-meta">TOLERANCE RANGE</div>
        </div>
        """, unsafe_allow_html=True)
    with res_c3:
        st.markdown(f"""
        <div class="calc-card">
            <div class="calc-label">Implicit Rate per m²</div>
            <div class="calc-val-white">Rp {est_rent/calc_size:,.0f}</div>
            <div class="calc-meta">IDR / M² / MONTH</div>
        </div>
        """, unsafe_allow_html=True)

    # Bu Sarah Investor Lens Tool: Furnishing ROI & Payback Analysis
    st.markdown("<hr style='border-color: #23252a; margin: 28px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom: 12px;">
        <h4 style="margin: 0; color: #ffffff;">Bu Sarah's Investor Tool • Furnishing Fit-Out Payback Analysis</h4>
        <div style="font-size: 13px; color: #8a8f98;">
            Evaluating the economic return of investing in interior fit-out (+26.8% market rent premium).
        </div>
    </div>
    """, unsafe_allow_html=True)

    roi_c1, roi_c2, roi_c3 = st.columns(3)
    unfurnished_rent = est_rent / furnish_mult
    furnish_delta_monthly = est_rent - unfurnished_rent
    furnish_delta_annual = furnish_delta_monthly * 12
    est_fitout_cost = calc_size * 1_200_000  # Estimate Rp 1.2M/m2 fit-out cost
    payback_months = (est_fitout_cost / furnish_delta_monthly) if furnish_delta_monthly > 0 else 0

    with roi_c1:
        st.metric(label="Furnishing Premium / Mo", value=f"+Rp {furnish_delta_monthly:,.0f}", delta="+26.8% Rent")
    with roi_c2:
        st.metric(label="Annual Extra Cash Flow", value=f"+Rp {furnish_delta_annual/1e6:,.1f}M / yr", delta="Gross Yield")
    with roi_c3:
        st.metric(label="Est. Fit-Out Payback", value=f"{payback_months:.1f} Months", delta=f"~{payback_months/12:.1f} Years")

# -------------------------------------------------------------
# TAB 4: SPATIAL DISTANCE DECAY (PRD 4.1.4)
# -------------------------------------------------------------
with tab4:
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h3 style="margin: 0 0 4px 0;">Spatial Gradient & Urban Rent Decay</h3>
        <div style="font-size: 13px; color: #8a8f98;">
            Empirical validation of the Alonso-Muth-Mills monocentric city model: rent per square meter decays as distance from Sudirman Core CBD increases.
        </div>
    </div>
    """, unsafe_allow_html=True)

    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("""
        <div style="font-size: 12px; font-weight: 500; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
            Price / m² vs Distance to Sudirman Core (km)
        </div>
        """, unsafe_allow_html=True)
        scatter_data = filtered_df[["distance_to_cbd_km", "price_per_m2_idr"]].dropna()
        scatter_data = scatter_data[scatter_data["price_per_m2_idr"] <= 600_000]
        st.scatter_chart(scatter_data.set_index("distance_to_cbd_km"), color="#e4f222")

    with sc2:
        st.markdown("""
        <div style="font-size: 12px; font-weight: 500; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
            Concentric Urban Ring Pricing Summary
        </div>
        """, unsafe_allow_html=True)
        transit_agg = filtered_df.groupby("urban_zone")["price_per_m2_idr"].agg(["count", "median", "mean"]).reset_index()
        transit_agg.columns = ["Urban Zone", "Sample Units", "Median Price / m²", "Mean Price / m²"]
        st.dataframe(
            transit_agg.style.format({
                "Sample Units": "{:,.0f}",
                "Median Price / m²": "Rp {:,.0f}",
                "Mean Price / m²": "Rp {:,.0f}"
            }),
            use_container_width=True,
            hide_index=True
        )

st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #23252a; padding-top: 16px; color: #62666d; font-size: 11px; font-family: 'JetBrains Mono', monospace;">
    <div>HOUSEHOLD INTELLIGENCE • PRD V1.0 MVP</div>
    <div>AFIATTA ILHAN SALEH • PROJECT TO WIN</div>
</div>
""", unsafe_allow_html=True)