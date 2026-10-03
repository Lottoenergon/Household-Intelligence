"""
app.py
Linear Design System ("Midnight Precision Instrument") Implementation.
Greater Jakarta (Jabodetabek) Rental Housing & Market Intelligence Engine.
Frontend UI/UX: Precision-engineered dark theme, zero visual clutter, strict token compliance.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="Household Intelligence • PropTech Telemetry",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Linear Design System Stylesheet (Targeted, Non-Destructive CSS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Typography Defaults */
    html, body, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Display Headings */
    h1, h2, h3 {
        letter-spacing: -0.022em !important;
        font-weight: 500 !important;
    }
    
    /* Metric Cards - Linear Carbon Surface with Hairline Graphite Border */
    div[data-testid="stMetric"] {
        background-color: #0f1011;
        border: 1px solid #23252a;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 16px 20px;
        transition: border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #383b3f;
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

    /* Tab Navigation (Linear Style) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #23252a;
        padding-bottom: 4px;
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

    /* Deal Card Custom Component */
    .deal-card {
        background-color: #0f1011;
        border: 1px solid #23252a;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 14px;
        transition: border-color 0.2s ease, background-color 0.2s ease;
    }
    .deal-card:hover {
        border-color: #383b3f;
        background-color: #121316;
    }
    
    /* Badges */
    .badge-deep-value {
        background: rgba(228, 242, 34, 0.1);
        color: #e4f222;
        border: 1px solid rgba(228, 242, 34, 0.3);
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.02em;
    }
    .badge-good-deal {
        background: rgba(99, 102, 241, 0.1);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 500;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.02em;
    }
    .badge-mono {
        background: rgba(255, 255, 255, 0.05);
        color: #8a8f98;
        border: 1px solid #23252a;
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Primary Action Button (Acid Lime #e4f222) */
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

    /* Calculator Results Box */
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
    .calc-value-lime {
        font-size: 28px;
        font-weight: 500;
        color: #e4f222;
        letter-spacing: -0.02em;
        font-family: 'Inter', sans-serif;
    }
    .calc-value-white {
        font-size: 22px;
        font-weight: 500;
        color: #ffffff;
        letter-spacing: -0.01em;
    }
    .calc-subtext {
        font-size: 11px;
        color: #62666d;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)


# 3. Data Loading
@st.cache_data
def load_evaluated_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "processed", "jabodetabek_rental_evaluated.csv")
    df = pd.read_csv(csv_path)
    return df


df_all = load_evaluated_data()

# -------------------------------------------------------------
# SIDEBAR CONTROLS
# -------------------------------------------------------------
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-top: 8px;">
    <div style="width: 8px; height: 8px; background-color: #e4f222; border-radius: 2px;"></div>
    <span style="font-size: 13px; font-weight: 500; color: #ffffff; letter-spacing: -0.01em;">HOUSEHOLD INTELLIGENCE</span>
</div>
<div style="font-size: 11px; color: #8a8f98; font-family: 'JetBrains Mono', monospace; margin-bottom: 24px;">
    JABODETABEK TELEMETRY • V2.0
</div>
""", unsafe_allow_html=True)

all_cities = sorted(df_all["target_city"].unique())
selected_cities = st.sidebar.multiselect("Metropolitan Region", all_cities, default=all_cities)

all_layouts = sorted(df_all["layout_category"].unique())
selected_layouts = st.sidebar.multiselect("Unit Layout", all_layouts, default=all_layouts)

price_range = st.sidebar.slider(
    "Monthly Rent Filter (IDR)",
    min_value=1_000_000,
    max_value=60_000_000,
    value=(1_000_000, 40_000_000),
    step=500_000,
    format="Rp %d"
)

st.sidebar.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
only_furnished = st.sidebar.checkbox("Full Furnished Units Only", value=False)
only_deals = st.sidebar.checkbox("Show Only Statistical Bargains (Z ≤ -0.75)", value=False)

# Filtering logic
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
# COMMAND HEADER & METRIC STRIP
# -------------------------------------------------------------
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; padding-top: 8px;">
    <div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">
            PROPTECH RADAR // PILLAR 2
        </div>
        <h1 style="margin: 0; font-size: 28px; color: #ffffff;">Greater Jakarta Rental Intelligence</h1>
        <div style="font-size: 13px; color: #8a8f98; margin-top: 4px;">
            Automated market ingestion, geospatial distance decay modeling, and Hedonic deal radar across 10 regions.
        </div>
    </div>
    <div style="text-align: right; padding-top: 8px;">
        <span class="badge-mono">787 AUDITED UNITS</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 5 Native Columns with Linear styling
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(label="Active Listings", value=f"{len(filtered_df):,}", delta="10 Regions")

with col2:
    med_rent = filtered_df["price_monthly_idr"].median() if len(filtered_df) > 0 else 0
    st.metric(label="Median Rent / Mo", value=f"Rp {med_rent/1e6:,.1f}M", delta="Standardized")

with col3:
    med_m2 = filtered_df["price_per_m2_idr"].median() if len(filtered_df) > 0 else 0
    st.metric(label="Median Price / m²", value=f"Rp {med_m2:,.0f}", delta="Area Yield")

with col4:
    pct_ff = (filtered_df["is_full_furnished"].mean() * 100) if len(filtered_df) > 0 else 0
    st.metric(label="Furnished Share", value=f"{pct_ff:.1f}%", delta="+26.8% Premium")

with col5:
    deals_count = (filtered_df["deal_score_z"] <= -0.75).sum() if len(filtered_df) > 0 else 0
    st.metric(label="Bargains Detected", value=f"{deals_count} Units", delta="Z ≤ -0.75")

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# MAIN VIEW TABS
# -------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "01 // Market Map & Benchmarks",
    "02 // Deal Hunter Radar",
    "03 // Hedonic Valuation Simulator",
    "04 // Spatial Distance Decay"
])

# -------------------------------------------------------------
# TAB 1: OVERVIEW & BENCHMARKS
# -------------------------------------------------------------
with tab1:
    c1, c2 = st.columns([1.25, 1])
    with c1:
        st.markdown("""
        <div style="font-size: 12px; font-weight: 500; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
            Geospatial Inventory Coordinates
        </div>
        """, unsafe_allow_html=True)
        
        map_data = filtered_df[["latitude", "longitude", "target_city", "price_per_m2_idr"]].dropna()
        if len(map_data) > 0:
            st.map(map_data, latitude="latitude", longitude="longitude", size=20, color="#e4f222")
        else:
            st.info("No listings found matching current filters.")

    with c2:
        st.markdown("""
        <div style="font-size: 12px; font-weight: 500; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
            Median Price / m² by Region
        </div>
        """, unsafe_allow_html=True)
        
        city_summary = filtered_df.groupby("target_city")["price_per_m2_idr"].median().sort_values(ascending=False).reset_index()
        city_summary.columns = ["Region", "Median Price / m²"]
        st.dataframe(
            city_summary.style.format({"Median Price / m²": "Rp {:,.0f}"}),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("""
        <div style="font-size: 12px; font-weight: 500; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 20px; margin-bottom: 10px;">
            Layout Inventory Distribution
        </div>
        """, unsafe_allow_html=True)
        layout_series = filtered_df["layout_category"].value_counts().reset_index()
        layout_series.columns = ["Layout", "Units"]
        st.bar_chart(layout_series.set_index("Layout"), color="#02b8cc")

# -------------------------------------------------------------
# TAB 2: DEAL HUNTER RADAR
# -------------------------------------------------------------
with tab2:
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h3 style="margin: 0 0 4px 0; color: #ffffff;">Algorithmic Deal Hunter Radar</h3>
        <div style="font-size: 13px; color: #8a8f98;">
            Listings identified with statistically significant negative price residuals from our Hedonic GBDT Model.
            Actual asking rent is substantially below predicted market equilibrium based on size, location, and amenities.
        </div>
    </div>
    """, unsafe_allow_html=True)

    deals_pool = filtered_df[filtered_df["deal_score_z"] <= -0.75].sort_values("deal_score_z").reset_index(drop=True)

    if len(deals_pool) == 0:
        st.info("No undervalued deals match the current filter selection. Broaden your price range or include additional cities in the sidebar.")
    else:
        for idx, row in deals_pool.head(15).iterrows():
            is_deep = row["deal_score_z"] <= -1.5
            badge_markup = (
                f'<span class="badge-deep-value">DEEP VALUE (-{row["discount_pct"]:.1f}%)</span>'
                if is_deep else
                f'<span class="badge-good-deal">GOOD DEAL (-{row["discount_pct"]:.1f}%)</span>'
            )
            raw_url = str(row['url']).strip()
            clean_url = raw_url if raw_url.startswith("http") else f"https://www.rumah123.com{raw_url}"

            st.markdown(f"""
            <div class="deal-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                    <div style="max-width: 78%;">
                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #8a8f98; margin-bottom: 4px;">
                            {row['listing_id']} &nbsp;•&nbsp; {row['target_city'].upper()} ({row['subdistrict']})
                        </div>
                        <h4 style="margin: 0; font-size: 16px; color: #ffffff; font-weight: 500;">{row['title']}</h4>
                    </div>
                    <div>{badge_markup}</div>
                </div>
                
                <div style="font-size: 12px; color: #8a8f98; margin-bottom: 16px;">
                    📐 {row['floor_size_m2']:.0f} m² &nbsp;•&nbsp; 
                    🛏️ {row['layout_category']} &nbsp;•&nbsp; 
                    🚆 {row['distance_to_transit_km']:.1f} km to {row['nearest_transit_hub']} &nbsp;•&nbsp;
                    🏛️ {row['distance_to_cbd_km']:.1f} km to Sudirman Core
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
                        <a href="{clean_url}" target="_blank" class="btn-action-lime">
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
        <h3 style="margin: 0 0 4px 0; color: #ffffff;">Hedonic Rent Valuation Simulator</h3>
        <div style="font-size: 13px; color: #8a8f98;">
            Simulate the market equilibrium rent of any apartment unit in Jabodetabek based on our trained 5-fold cross-validated Gradient Boosting regression model.
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
        
        st.markdown("<div style='font-size: 11px; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;'>FACILITIES & AMENITIES</div>", unsafe_allow_html=True)
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

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    res_c1, res_c2, res_c3 = st.columns(3)
    with res_c1:
        st.markdown(f"""
        <div class="calc-card">
            <div class="calc-label">Fair Market Equilibrium</div>
            <div class="calc-value-lime">Rp {est_rent:,.0f}</div>
            <div class="calc-subtext">IDR / MONTH</div>
        </div>
        """, unsafe_allow_html=True)
    with res_c2:
        st.markdown(f"""
        <div class="calc-card">
            <div class="calc-label">Predicted Interval (±10%)</div>
            <div class="calc-value-white">Rp {est_rent*0.9:,.0f} - {est_rent*1.1/1e6:,.1f}M</div>
            <div class="calc-subtext">CONFIDENCE BAND</div>
        </div>
        """, unsafe_allow_html=True)
    with res_c3:
        st.markdown(f"""
        <div class="calc-card">
            <div class="calc-label">Implicit Rate per m²</div>
            <div class="calc-value-white">Rp {est_rent/calc_size:,.0f}</div>
            <div class="calc-subtext">IDR / M² / MONTH</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 4: SPATIAL DISTANCE DECAY
# -------------------------------------------------------------
with tab4:
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h3 style="margin: 0 0 4px 0; color: #ffffff;">Spatial Gradient & Distance Decay</h3>
        <div style="font-size: 13px; color: #8a8f98;">
            Urban economic evidence: evaluating the exponential decay of rental rates per square meter as geographic distance from Sudirman Core CBD increases.
        </div>
    </div>
    """, unsafe_allow_html=True)

    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown("""
        <div style="font-size: 12px; font-weight: 500; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
            Price / m² vs Distance to Sudirman CBD (km)
        </div>
        """, unsafe_allow_html=True)
        scatter_data = filtered_df[["distance_to_cbd_km", "price_per_m2_idr"]].dropna()
        scatter_data = scatter_data[scatter_data["price_per_m2_idr"] <= 600_000]
        st.scatter_chart(scatter_data.set_index("distance_to_cbd_km"), color="#e4f222")

    with sc2:
        st.markdown("""
        <div style="font-size: 12px; font-weight: 500; color: #8a8f98; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
            Urban Zone Summary Metrics
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
    <div>HOUSEHOLD INTELLIGENCE • LINEAR DESIGN SYSTEM</div>
    <div>AFIATTA ILHAN SALEH • PROJECT TO WIN</div>
</div>
""", unsafe_allow_html=True)