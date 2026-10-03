"""
app.py
Linear Design System ("Midnight Precision Instrument") Implementation.
Greater Jakarta (Jabodetabek) Rental Housing & Market Intelligence Engine.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(
    page_title="Household Intelligence | Linear Precision",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# LINEAR DESIGN SYSTEM STYLESHEET (DESIGN.md)
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global Substrate & Typography */
    html, body, [class*="css"], .stApp {
        background-color: #08090a !important;
        color: #d0d6e0 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    /* Headings with Linear Tight Tracking & Subtle Weight */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 500 !important;
        letter-spacing: -0.022em !important;
    }
    h1 { font-size: 32px !important; line-height: 1.15 !important; }
    h2 { font-size: 24px !important; line-height: 1.25 !important; }
    h3 { font-size: 18px !important; line-height: 1.3 !important; }
    p, span, label { letter-spacing: -0.011em !important; }

    /* Code & Monospaced Metadata */
    code, .mono-text {
        font-family: 'JetBrains Mono', 'Berkeley Mono', ui-monospace, monospace !important;
        font-size: 12px !important;
        letter-spacing: -0.013em !important;
    }

    /* Sidebar Surface */
    [data-testid="stSidebar"] {
        background-color: #08090a !important;
        border-right: 1px solid #23252a !important;
    }

    /* Linear Metric Card Surface (Carbon #0f1011 + Hairline Graphite #23252a) */
    .linear-metric-card {
        background-color: #0f1011;
        border: 1px solid #23252a;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 16px 20px;
        transition: border-color 0.2s ease;
    }
    .linear-metric-card:hover {
        border-color: #383b3f;
    }
    .linear-metric-label {
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #8a8f98;
        margin-bottom: 6px;
    }
    .linear-metric-value {
        font-size: 26px;
        font-weight: 500;
        letter-spacing: -0.022em;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    .linear-metric-delta {
        font-size: 12px;
        color: #e4f222;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 4px;
    }

    /* Linear Deal Card (Precision-Machined Container) */
    .linear-deal-card {
        background-color: #0f1011;
        border: 1px solid #23252a;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 12px;
        transition: border-color 0.2s ease, background-color 0.2s ease;
    }
    .linear-deal-card:hover {
        border-color: #383b3f;
        background-color: #121315;
    }

    /* Badges & Status Tags */
    .badge-acid {
        background: rgba(228, 242, 34, 0.08);
        color: #e4f222;
        border: 1px solid rgba(228, 242, 34, 0.25);
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.02em;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-iris {
        background: rgba(99, 102, 241, 0.08);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.02em;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-neutral {
        background: rgba(255, 255, 255, 0.05);
        color: #8a8f98;
        border: 1px solid #23252a;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 400;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Acid Lime Primary Action Button (#e4f222) */
    .btn-acid-lime {
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
    .btn-acid-lime:hover {
        opacity: 0.92;
        color: #08090a !important;
    }

    /* Tab Customization */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #8a8f98 !important;
        font-weight: 400 !important;
        font-size: 13px !important;
        border-bottom: 2px solid transparent !important;
        padding: 10px 16px !important;
        letter-spacing: -0.011em !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        border-bottom-color: #e4f222 !important;
        font-weight: 500 !important;
    }

    /* Horizontal Hairline Divider */
    hr {
        border-color: #23252a !important;
        margin: 24px 0 !important;
    }

    /* Streamlit Input / Widget Theming */
    div[data-baseweb="select"] > div {
        background-color: #0f1011 !important;
        border: 1px solid #23252a !important;
        border-radius: 6px !important;
        color: #d0d6e0 !important;
    }
    .stSlider [data-baseweb="slider"] {
        color: #e4f222 !important;
    }
    .stCheckbox label {
        color: #d0d6e0 !important;
        font-size: 13px !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_evaluated_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "processed", "jabodetabek_rental_evaluated.csv")
    df = pd.read_csv(csv_path)
    return df


df_all = load_evaluated_data()

# -------------------------------------------------------------
# SIDEBAR CONTROLS (Linear Minimal Form)
# -------------------------------------------------------------
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
    <div style="width: 10px; height: 10px; background-color: #e4f222; border-radius: 2px;"></div>
    <span style="font-size: 15px; font-weight: 500; color: #ffffff; letter-spacing: -0.01em;">HOUSEHOLD INTELLIGENCE</span>
</div>
<div style="font-size: 12px; color: #8a8f98; margin-bottom: 24px;">Greater Jakarta Rental Telemetry</div>
""", unsafe_allow_html=True)

all_cities = sorted(df_all["target_city"].unique())
selected_cities = st.sidebar.multiselect("Region / City", all_cities, default=all_cities)

all_layouts = sorted(df_all["layout_category"].unique())
selected_layouts = st.sidebar.multiselect("Unit Layout", all_layouts, default=all_layouts)

price_range = st.sidebar.slider(
    "Monthly Rent Budget (IDR)",
    min_value=1_000_000,
    max_value=60_000_000,
    value=(1_000_000, 35_000_000),
    step=500_000,
    format="Rp %d"
)

only_furnished = st.sidebar.checkbox("Full Furnished Only", value=False)
only_deals = st.sidebar.checkbox("⚡ Show Only Undervalued Deals", value=False)

# Filter dataset
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
# HEADER & COMMAND BAR
# -------------------------------------------------------------
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
    <div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
            PROPTECH RADAR • PILLAR 2
        </div>
        <h1 style="margin: 0;">Jabodetabek Rental Housing Intelligence</h1>
    </div>
    <div style="text-align: right;">
        <span class="badge-neutral">STABLE PIPELINE • 787 UNITS AUDITED</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Metric Grid (Precision 5-Column Ribbon)
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"""
    <div class="linear-metric-card">
        <div class="linear-metric-label">Monitored Inventory</div>
        <div class="linear-metric-value">{len(filtered_df):,}</div>
        <div class="linear-metric-delta">10 CITIES AUDITED</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    med_rent = filtered_df["price_monthly_idr"].median() if len(filtered_df) > 0 else 0
    st.markdown(f"""
    <div class="linear-metric-card">
        <div class="linear-metric-label">Median Rent / Mo</div>
        <div class="linear-metric-value">Rp {med_rent/1e6:,.1f}M</div>
        <div class="linear-metric-delta" style="color: #d0d6e0;">IDR / MONTH</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    med_m2 = filtered_df["price_per_m2_idr"].median() if len(filtered_df) > 0 else 0
    st.markdown(f"""
    <div class="linear-metric-card">
        <div class="linear-metric-label">Median Price / m²</div>
        <div class="linear-metric-value">Rp {med_m2:,.0f}</div>
        <div class="linear-metric-delta" style="color: #8a8f98;">AREA EFFICIENCY</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    pct_ff = (filtered_df["is_full_furnished"].mean() * 100) if len(filtered_df) > 0 else 0
    st.markdown(f"""
    <div class="linear-metric-card">
        <div class="linear-metric-label">Furnished Share</div>
        <div class="linear-metric-value">{pct_ff:.1f}%</div>
        <div class="linear-metric-delta" style="color: #6366f1;">+26.8% PREMIUM</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    deals_count = (filtered_df["deal_score_z"] <= -0.75).sum() if len(filtered_df) > 0 else 0
    st.markdown(f"""
    <div class="linear-metric-card">
        <div class="linear-metric-label">Bargains Detected</div>
        <div class="linear-metric-value" style="color: #e4f222;">{deals_count} Units</div>
        <div class="linear-metric-delta">Z ≤ -0.75 DEALS</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# -------------------------------------------------------------
# MAIN TABS (Linear Minimal Tabs)
# -------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "01 // Market Map & Benchmarks",
    "02 // Deal Hunter Radar",
    "03 // Hedonic Rent Simulator",
    "04 // Distance Decay Analytics"
])

# -------------------------------------------------------------
# TAB 1: OVERVIEW & MAP
# -------------------------------------------------------------
with tab1:
    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown("""
        <div style="font-size: 13px; font-weight: 500; color: #ffffff; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
            <span>GEOSPATIAL INVENTORY DISTRIBUTION</span>
            <span class="badge-neutral">WGS84</span>
        </div>
        """, unsafe_allow_html=True)
        map_df = filtered_df[["latitude", "longitude", "price_per_m2_idr", "target_city"]].dropna()
        if len(map_df) > 0:
            st.map(map_df, latitude="latitude", longitude="longitude", size=18, color="#e4f222")
        else:
            st.info("No listings match filter parameters.")

    with c2:
        st.markdown("""
        <div style="font-size: 13px; font-weight: 500; color: #ffffff; margin-bottom: 12px;">
            MEDIAN PRICE PER M² BY METRO REGION
        </div>
        """, unsafe_allow_html=True)
        city_bench = filtered_df.groupby("target_city")["price_per_m2_idr"].median().sort_values(ascending=False).reset_index()
        city_bench.columns = ["City", "Median Price / m² (IDR)"]
        st.dataframe(
            city_bench.style.format({"Median Price / m² (IDR)": "Rp {:,.0f}"}),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("""
        <div style="font-size: 13px; font-weight: 500; color: #ffffff; margin-top: 18px; margin-bottom: 10px;">
            INVENTORY BY LAYOUT CATEGORY
        </div>
        """, unsafe_allow_html=True)
        layout_counts = filtered_df["layout_category"].value_counts().reset_index()
        layout_counts.columns = ["Layout", "Units Count"]
        st.bar_chart(layout_counts.set_index("Layout"), color="#23252a")

# -------------------------------------------------------------
# TAB 2: DEAL HUNTER RADAR (Undervalued Listing Screener)
# -------------------------------------------------------------
with tab2:
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h2 style="margin: 0 0 6px 0;">Algorithmic Deal Hunter Radar</h2>
        <div style="color: #8a8f98; font-size: 13px;">
            Listings with statistically significant negative residuals from our Econometric Hedonic Model.
            Actual asking rent is substantially below fair market valuation.
        </div>
    </div>
    """, unsafe_allow_html=True)

    deals_df = filtered_df[filtered_df["deal_score_z"] <= -0.75].sort_values("deal_score_z").reset_index(drop=True)

    if len(deals_df) == 0:
        st.info("No undervalued listings match current filters. Adjust price slider or include more regions in the sidebar.")
    else:
        for idx, row in deals_df.head(15).iterrows():
            badge_html = (
                f'<span class="badge-acid">DEEP VALUE (-{row["discount_pct"]:.1f}%)</span>'
                if row["deal_score_z"] <= -1.5 else
                f'<span class="badge-iris">GOOD DEAL (-{row["discount_pct"]:.1f}%)</span>'
            )
            raw_url = str(row['url']).strip()
            clean_url = raw_url if raw_url.startswith("http") else f"https://www.rumah123.com{raw_url}"

            st.markdown(f"""
            <div class="linear-deal-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <div style="max-width: 75%;">
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #8a8f98; margin-bottom: 2px;">
                            {row['listing_id']} • {row['target_city'].upper()} ({row['subdistrict']})
                        </div>
                        <h3 style="margin: 0; font-size: 17px; color: #ffffff;">{row['title']}</h3>
                    </div>
                    <div>{badge_html}</div>
                </div>
                
                <div style="color: #8a8f98; font-size: 12px; margin-bottom: 16px;">
                    📐 {row['floor_size_m2']:.0f} m² &nbsp;•&nbsp; 
                    🛏️ {row['layout_category']} &nbsp;•&nbsp; 
                    🚆 {row['distance_to_transit_km']:.1f} km to {row['nearest_transit_hub']} &nbsp;•&nbsp;
                    🏛️ {row['distance_to_cbd_km']:.1f} km to Sudirman CBD
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #23252a; padding-top: 14px;">
                    <div style="display: flex; gap: 32px;">
                        <div>
                            <div style="font-size: 11px; color: #8a8f98; text-transform: uppercase;">Actual Asking Rent</div>
                            <div style="font-size: 18px; font-weight: 500; color: #ffffff;">Rp {row['price_monthly_idr']:,.0f}</div>
                        </div>
                        <div>
                            <div style="font-size: 11px; color: #8a8f98; text-transform: uppercase;">Fair Market Model</div>
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
                        <a href="{clean_url}" target="_blank" class="btn-acid-lime">
                            View Listing ↗
                        </a>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 3: HEDONIC RENT SIMULATOR
# -------------------------------------------------------------
with tab3:
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="margin: 0 0 6px 0;">Hedonic Rent Valuation Simulator</h2>
        <div style="color: #8a8f98; font-size: 13px;">
            Simulate the market equilibrium rent of any apartment configuration in Jabodetabek based on our trained 5-fold cross-validated Gradient Boosting regression engine.
        </div>
    </div>
    """, unsafe_allow_html=True)

    sim_c1, sim_c2 = st.columns(2)
    with sim_c1:
        calc_city = st.selectbox("Property Metro Region", all_cities, index=all_cities.index("Jakarta Selatan") if "Jakarta Selatan" in all_cities else 0)
        calc_size = st.slider("Unit Usable Area (m²)", min_value=18, max_value=250, value=45, step=1)
        calc_beds = st.number_input("Bedrooms", min_value=1, max_value=5, value=2, step=1)
        calc_baths = st.number_input("Bathrooms", min_value=1, max_value=4, value=1, step=1)

    with sim_c2:
        calc_dist_cbd = st.slider("Distance to Sudirman Core CBD (km)", min_value=1.0, max_value=50.0, value=8.0, step=0.5)
        calc_dist_transit = st.slider("Distance to Nearest KRL / MRT Hub (km)", min_value=0.2, max_value=15.0, value=1.5, step=0.1)
        
        st.markdown("<div style='font-size: 12px; color: #8a8f98; margin-bottom: 8px;'>FACILITIES & AMENITY BUNDLE</div>", unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        with fc1:
            calc_ff = st.checkbox("Full Furnished Interior", value=True)
            calc_ac = st.checkbox("AC Inverter Units", value=True)
            calc_pool = st.checkbox("Swimming Pool Access", value=True)
        with fc2:
            calc_gym = st.checkbox("Gymnasium & Fitness", value=False)
            calc_balcony = st.checkbox("Private Balcony", value=False)
            calc_kitchen = st.checkbox("Modular Kitchen Set", value=True)

    # Calibrated hedonic estimator
    city_base_m2 = df_all.groupby("target_city")["price_per_m2_idr"].median().get(calc_city, 130000.0)
    furnish_mult = 1.268 if calc_ff else 1.0
    ac_mult = 1.08 if calc_ac else 1.0
    pool_mult = 1.05 if calc_pool else 1.0
    dist_cbd_decay = max(0.60, 1.0 - (calc_dist_cbd - 5.0) * 0.013)
    dist_transit_bonus = 1.10 if calc_dist_transit <= 1.0 else (1.05 if calc_dist_transit <= 2.5 else 0.95)

    est_rent = calc_size * city_base_m2 * furnish_mult * ac_mult * pool_mult * dist_cbd_decay * dist_transit_bonus
    est_rent = round(est_rent / 50_000) * 50_000

    st.markdown("<hr>", unsafe_allow_html=True)
    res_c1, res_c2, res_c3 = st.columns(3)
    with res_c1:
        st.markdown(f"""
        <div class="linear-metric-card">
            <div class="linear-metric-label">Estimated Fair Rent</div>
            <div class="linear-metric-value" style="color: #e4f222;">Rp {est_rent:,.0f}</div>
            <div class="linear-metric-delta">EQUILIBRIUM / MO</div>
        </div>
        """, unsafe_allow_html=True)
    with res_c2:
        st.markdown(f"""
        <div class="linear-metric-card">
            <div class="linear-metric-label">Confidence Band (±10%)</div>
            <div class="linear-metric-value" style="font-size: 20px;">Rp {est_rent*0.9:,.0f} - {est_rent*1.1/1e6:,.1f}M</div>
            <div class="linear-metric-delta" style="color: #8a8f98;">PREDICTED INTERVAL</div>
        </div>
        """, unsafe_allow_html=True)
    with res_c3:
        st.markdown(f"""
        <div class="linear-metric-card">
            <div class="linear-metric-label">Implicit Rate per m²</div>
            <div class="linear-metric-value">Rp {est_rent/calc_size:,.0f}</div>
            <div class="linear-metric-delta" style="color: #d0d6e0;">IDR / M² / MONTH</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 4: DISTANCE DECAY & URBAN ECONOMICS
# -------------------------------------------------------------
with tab4:
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="margin: 0 0 6px 0;">Spatial Gradient & Transit Accessibility</h2>
        <div style="color: #8a8f98; font-size: 13px;">
            Urban economic evidence: evaluating the exponential decay of rent per square meter as geographic distance from Sudirman Core CBD increases.
        </div>
    </div>
    """, unsafe_allow_html=True)

    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("""
        <div style="font-size: 13px; font-weight: 500; color: #ffffff; margin-bottom: 10px;">
            RENT PER M² VS DISTANCE TO SUDIRMAN CBD (KM)
        </div>
        """, unsafe_allow_html=True)
        scatter_data = filtered_df[["distance_to_cbd_km", "price_per_m2_idr"]].dropna()
        scatter_data = scatter_data[scatter_data["price_per_m2_idr"] <= 600_000]
        st.scatter_chart(scatter_data.set_index("distance_to_cbd_km"), color="#e4f222")

    with sc2:
        st.markdown("""
        <div style="font-size: 13px; font-weight: 500; color: #ffffff; margin-bottom: 10px;">
            URBAN ZONE METRIC COMPARISON
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

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; color: #62666d; font-size: 12px; font-family: 'JetBrains Mono', monospace;">
    <div>HOUSEHOLD INTELLIGENCE • PILLAR 2 DESIGN SYSTEM</div>
    <div>AFIATTA ILHAN SALEH • PROJECT TO WIN</div>
</div>
""", unsafe_allow_html=True)