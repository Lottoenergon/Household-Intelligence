"""
app.py
Interactive Market Intelligence & Rental Housing Dashboard (Streamlit).
Greater Jakarta (Jabodetabek) PropTech Intelligence Engine.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(
    page_title="Jabodetabek Rental Intelligence | PropTech Deal Finder",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .deal-badge {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "processed", "jabodetabek_rental_evaluated.csv")
    if not os.path.exists(csv_path):
        st.error(f"Dataset not found at {csv_path}. Please run pipeline first.")
        st.stop()
    df = pd.read_csv(csv_path)
    return df


df_raw = load_data()

# Sidebar Controls
st.sidebar.image("https://img.icons8.com/isometric/100/apartment.png", width=70)
st.sidebar.title("Rental Intelligence")
st.sidebar.caption("PropTech Valuation & Market Analytics Engine")

# Filter City
all_cities = sorted(df_raw["target_city"].unique().tolist())
selected_cities = st.sidebar.multiselect(
    "📍 Select Cities (Jabodetabek)",
    options=all_cities,
    default=all_cities
)

# Filter Budget
min_p = int(df_raw["price_monthly_idr"].min() / 1_000_000)
max_p = int(df_raw["price_monthly_idr"].max() / 1_000_000)
budget_range = st.sidebar.slider(
    "💰 Monthly Budget (Juta IDR)",
    min_value=min_p,
    max_value=max_p,
    value=(min_p, 25),
    step=1
)

# Filter Bedrooms
all_br = sorted(df_raw["bedrooms"].unique().tolist())
selected_br = st.sidebar.multiselect(
    "🛏️ Bedrooms",
    options=all_br,
    default=all_br
)

# Filter Valuation Deal
deal_types = ["All Listings", "Good Deals Only (>10% Discount)", "High Value Deals (>25% Discount)"]
selected_deal_type = st.sidebar.selectbox("🎯 Valuation Filter", options=deal_types)

# Apply Filter
df_filtered = df_raw[
    (df_raw["target_city"].isin(selected_cities)) &
    (df_raw["price_monthly_idr"] >= budget_range[0] * 1_000_000) &
    (df_raw["price_monthly_idr"] <= budget_range[1] * 1_000_000) &
    (df_raw["bedrooms"].isin(selected_br))
].copy()

if selected_deal_type == "Good Deals Only (>10% Discount)":
    df_filtered = df_filtered[df_filtered["undervalued_discount_pct"] >= 10.0]
elif selected_deal_type == "High Value Deals (>25% Discount)":
    df_filtered = df_filtered[df_filtered["undervalued_discount_pct"] >= 25.0]

# --- MAIN DASHBOARD ---
st.title("🏢 Jabodetabek Rental Housing Intelligence Engine")
st.markdown("""
*Analyzing real-world rental supply, price per m², and machine-learning fair-value deviations across Greater Jakarta.*
""")

# Top KPI Metrics
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Total Active Listings", f"{len(df_filtered):,} units", delta=f"{len(df_filtered) - len(df_raw)} filtered")
with kpi2:
    med_rent = df_filtered["price_monthly_idr"].median() if len(df_filtered) > 0 else 0
    st.metric("Median Monthly Rent", f"Rp {med_rent:,.0f}" if med_rent > 0 else "N/A")
with kpi3:
    med_m2 = df_filtered["price_per_m2_idr"].median() if len(df_filtered) > 0 else 0
    st.metric("Median Rent / m²", f"Rp {med_m2:,.0f}" if med_m2 > 0 else "N/A")
with kpi4:
    deals_count = len(df_filtered[df_filtered["undervalued_discount_pct"] >= 15.0])
    st.metric("Undervalued Deals Found", f"{deals_count} units", delta="Deal Hunter Radar")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🎯 Top Undervalued Deals", "📊 Market Benchmarks & Price/m²", "🗺️ Geographic Map"])

with tab1:
    st.subheader("Radar Peluang Sewa: Unit Undervalued di Bawah Harga Pasar")
    st.caption("Algoritma Hedonic Pricing memprediksi nilai wajar unit berdasarkan kota, luas kamar (m²), jumlah kamar tidur, dan fasilitas.")
    
    top_deals = df_filtered.sort_values("undervalued_discount_pct", ascending=False).head(15)
    
    if len(top_deals) == 0:
        st.info("No listings match the current filters.")
    else:
        for _, row in top_deals.iterrows():
            with st.container():
                c_img, c_info, c_price = st.columns([1.5, 3.5, 2])
                with c_img:
                    if pd.notnull(row["image_url"]) and str(row["image_url"]).startswith("http"):
                        st.image(row["image_url"], use_container_width=True)
                    else:
                        st.write("📷 *No Image Available*")
                with c_info:
                    st.markdown(f"**[{row['target_city']}] {row['title']}**")
                    st.write(f"📍 {row['display_location']}")
                    st.caption(f"📐 {row['floor_size_m2']} m² | 🛏️ {row['bedrooms']} KT | 🚿 {row['bathrooms']} KM | Furnish: {'Full' if row['is_full_furnished'] else ('Semi' if row['is_semi_furnished'] else 'Bare')}")
                    if pd.notnull(row["url"]):
                        st.markdown(f"[🔗 Lihat Listing Asli]({row['url']})")
                with c_price:
                    st.metric("Actual Rent", f"Rp {row['price_monthly_idr']:,.0f} /bln")
                    st.caption(f"Fair Market Est: Rp {row['estimated_fair_price']:,.0f}")
                    discount = row["undervalued_discount_pct"]
                    if discount > 0:
                        st.success(f"🔥 {discount:.1f}% UNDERVALUED")
                    else:
                        st.warning(f"⚠️ {abs(discount):.1f}% Above Market")
                st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)

with tab2:
    st.subheader("Price per m² & Layout Analysis")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("**Median Price per m² by City (IDR)**")
        city_stats = df_filtered.groupby("target_city")["price_per_m2_idr"].median().sort_values(ascending=True)
        st.bar_chart(city_stats)

    with col_chart2:
        st.markdown("**Monthly Rent by Bedroom Layout (IDR)**")
        br_stats = df_filtered.groupby("bedrooms")["price_monthly_idr"].median()
        st.bar_chart(br_stats)

    st.markdown("### City Aggregate Comparison")
    summary_table = df_filtered.groupby("target_city").agg(
        Total_Units=("listing_id", "count"),
        Median_Rent=("price_monthly_idr", "median"),
        Median_Price_m2=("price_per_m2_idr", "median"),
        Avg_Size_m2=("floor_size_m2", "mean")
    ).reset_index()
    summary_table["Median_Rent"] = summary_table["Median_Rent"].apply(lambda x: f"Rp {x:,.0f}")
    summary_table["Median_Price_m2"] = summary_table["Median_Price_m2"].apply(lambda x: f"Rp {x:,.0f}")
    summary_table["Avg_Size_m2"] = summary_table["Avg_Size_m2"].round(1)
    st.dataframe(summary_table, use_container_width=True)

with tab3:
    st.subheader("Geographic Distribution of Units")
    geo_df = df_filtered.dropna(subset=["latitude", "longitude"])
    if len(geo_df) > 0:
        st.map(geo_df[["latitude", "longitude"]])
        st.caption(f"Displaying {len(geo_df)} units with verified GPS coordinates.")
    else:
        st.info("No coordinates available for current filter selection.")
