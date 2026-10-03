"""
transformation.py
Production Data Transformation, Cleaning & Geospatial Feature Engineering Pipeline.
Transforms staged raw JSON listings into normalized, feature-rich tabular datasets.
Includes:
- Price normalization to standard monthly rent (IDR).
- Outlier filtering & sale ads purge.
- Haversine geospatial calculations to Jakarta CBD & regional transit hubs.
- NLP keyword extraction for furnishing levels and amenities.
- Sub-district parsing and layout classification.
"""

import os
import sys
import re
import json
import logging
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Core Business Reference Coordinates (WGS84)
JAKARTA_CBD_COORDS = (-6.2088, 106.8200)  # Sudirman - Thamrin Prime Axis

KEY_TRANSIT_HUBS = {
    "Stasiun KRL Manggarai": (-6.2099, 106.8502),
    "Stasiun MRT Dukuh Atas": (-6.2008, 106.8227),
    "Stasiun MRT Lebak Bulus": (-6.2890, 106.7745),
    "Stasiun MRT Blok M": (-6.2443, 106.7979),
    "Stasiun KRL Tanah Abang": (-6.1855, 106.8110),
    "Stasiun KRL Depok Baru": (-6.3912, 106.8219),
    "Stasiun KRL Tangerang": (-6.1767, 106.6329),
    "Stasiun KRL Bekasi": (-6.2361, 106.9995),
    "Stasiun KRL Bogor": (-6.5952, 106.7903),
    "Stasiun KRL Rawabuntu (BSD)": (-6.3216, 106.6806),
    "Stasiun KRL Jurang Mangu (Bintaro)": (-6.2905, 106.7265)
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two geographic coordinates in kilometers."""
    R = 6371.0  # Earth radius in km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return float(R * c)


def parse_normalized_price(raw_val: str) -> Tuple[float, str, bool]:
    """
    Parses Indonesian price string and converts to standardized monthly rent in IDR.
    Detects ad listings with sale prices (Miliar) that do not belong to rental.
    """
    if not isinstance(raw_val, str) or not raw_val.strip():
        return np.nan, "unknown", False

    s = raw_val.lower().replace("rp", "").strip()
    
    # Flag primary sales ads mistakenly in rental feed
    if "miliar" in s or " m " in f" {s} ":
        if not ("tahun" in s or "bulan" in s):
            return np.nan, "sale_outlier", True

    is_yearly = "/tahun" in s or "tahun" in s
    is_daily = "/hari" in s or "hari" in s
    is_monthly = "/bulan" in s or "bulan" in s or (not is_yearly and not is_daily)

    clean_s = re.sub(r'/(bulan|tahun|hari)', '', s).strip()
    
    m_jt = re.search(r'([\d\.,]+)\s*(?:juta|jt)', clean_s)
    m_m = re.search(r'([\d\.,]+)\s*(?:miliar|m)', clean_s)
    m_rb = re.search(r'([\d\.,]+)\s*(?:ribu|rb)', clean_s)

    num = None
    if m_jt:
        raw_num = m_jt.group(1).replace(".", "").replace(",", ".")
        try:
            num = float(raw_num) * 1_000_000
        except ValueError:
            pass
    elif m_m:
        raw_num = m_m.group(1).replace(".", "").replace(",", ".")
        try:
            num = float(raw_num) * 1_000_000_000
        except ValueError:
            pass
    elif m_rb:
        raw_num = m_rb.group(1).replace(".", "").replace(",", ".")
        try:
            num = float(raw_num) * 1_000
        except ValueError:
            pass
    else:
        digits = re.sub(r'[^\d]', '', clean_s)
        if digits:
            try:
                num = float(digits)
            except ValueError:
                pass

    if num is None or num <= 0:
        return np.nan, "invalid", False

    if is_yearly:
        monthly_price = num / 12.0
        period = "yearly"
    elif is_daily:
        monthly_price = num * 30.0
        period = "daily"
    else:
        monthly_price = num
        period = "monthly"

    # Extreme filter: realistic monthly rent range (Rp 600k - Rp 180 Jt/bln)
    is_outlier = (monthly_price < 600_000) or (monthly_price > 180_000_000)
    return monthly_price, period, is_outlier


def extract_amenity_features(title: str, desc: str) -> Dict[str, int]:
    """
    NLP keyword extraction for apartment amenities from Indonesian property descriptions.
    """
    combined_text = f"{str(title).lower()} {str(desc).lower()}"
    
    # 1. Furnishing status
    is_full_furnished = int(bool(re.search(r'\bfull(?:y)?\s*(?:furnished|furnish)|\bfff\b', combined_text)))
    is_semi_furnished = int(bool(re.search(r'\bsemi\s*(?:furnished|furnish)\b', combined_text)))
    is_unfurnished = int(bool(re.search(r'\bunfurnished|\bnon\s*furnish|\bkosongan?\b', combined_text)))
    
    # 2. Specific Amenities
    has_ac = int(bool(re.search(r'\bac\b|air\s*conditioner', combined_text)))
    has_wifi = int(bool(re.search(r'\bwifi\b|internet|indihome|biznet', combined_text)))
    has_water_heater = int(bool(re.search(r'water\s*heater|pemanas\s*air', combined_text)))
    has_pool = int(bool(re.search(r'kolam\s*renang|swimming\s*pool|\bpool\b', combined_text)))
    has_gym = int(bool(re.search(r'\bgym\b|fitness|pusat\s*kebugaran', combined_text)))
    has_balcony = int(bool(re.search(r'balcon|balkon', combined_text)))
    has_kitchen = int(bool(re.search(r'kitchen\s*set|dapur|kompor', combined_text)))
    near_transit = int(bool(re.search(r'\bmrt\b|\blrt\b|\bkrl\b|\bstasiun\b|\btransjakarta\b|\bbusway\b', combined_text)))
    has_parking = int(bool(re.search(r'parkir|parking', combined_text)))

    return {
        "is_full_furnished": is_full_furnished,
        "is_semi_furnished": is_semi_furnished,
        "is_unfurnished": is_unfurnished,
        "has_ac": has_ac,
        "has_wifi": has_wifi,
        "has_water_heater": has_water_heater,
        "has_pool": has_pool,
        "has_gym": has_gym,
        "has_balcony": has_balcony,
        "has_kitchen": has_kitchen,
        "near_transit": near_transit,
        "has_parking": has_parking
    }


def clean_and_transform_pipeline(raw_json_path: str, output_dir: str = "data/processed") -> pd.DataFrame:
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Loading raw staged JSON from {raw_json_path}...")
    
    with open(raw_json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    df = pd.DataFrame(raw_data)
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} raw records.")

    # 1. Deduplication on URL and title
    df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)
    logger.info(f"Deduplicated by URL: {len(df)} remaining (-{initial_count - len(df)} duplicates).")

    # 2. Parse price & rental duration
    price_res = [parse_normalized_price(p) for p in df["raw_price"]]
    df["price_monthly_idr"] = [r[0] for r in price_res]
    df["original_period"] = [r[1] for r in price_res]
    df["is_price_outlier"] = [r[2] for r in price_res]

    # Filter out invalid prices and sale outliers
    valid_mask = df["price_monthly_idr"].notnull() & (~df["is_price_outlier"])
    df_valid = df[valid_mask].copy().reset_index(drop=True)
    logger.info(f"Price validation complete: {len(df_valid)} valid rentals remaining (-{len(df) - len(df_valid)} outliers/ads).")

    # 3. Clean numeric fields (bedrooms, bathrooms, floor_size)
    df_valid["bedrooms"] = pd.to_numeric(df_valid["bedrooms"], errors="coerce").fillna(1).astype(int)
    df_valid["bathrooms"] = pd.to_numeric(df_valid["bathrooms"], errors="coerce").fillna(1).astype(int)
    
    # Layout Category
    def classify_layout(br: int) -> str:
        if br <= 1:
            return "Studio / 1BR"
        elif br == 2:
            return "2 Bedroom"
        elif br == 3:
            return "3 Bedroom"
        else:
            return "4+ Bedroom"

    df_valid["layout_category"] = df_valid["bedrooms"].apply(classify_layout)

    # Impute missing floor size by median of same bedroom count in same city
    df_valid["floor_size_m2"] = pd.to_numeric(df_valid["floor_size_m2"], errors="coerce")
    median_by_br = df_valid.groupby(["target_city", "bedrooms"])["floor_size_m2"].transform("median")
    fallback_median = df_valid.groupby("bedrooms")["floor_size_m2"].transform("median")
    df_valid["floor_size_m2"] = df_valid["floor_size_m2"].fillna(median_by_br).fillna(fallback_median).fillna(36.0)
    
    # Floor size realistic bounds (15 m2 studio to 350 m2 penthouse)
    df_valid = df_valid[(df_valid["floor_size_m2"] >= 15) & (df_valid["floor_size_m2"] <= 350)].copy()

    # 4. Calculate Price per m2 (Key Real Estate Metric)
    df_valid["price_per_m2_idr"] = df_valid["price_monthly_idr"] / df_valid["floor_size_m2"]

    # 5. Extract NLP amenity vectors
    amenity_records = [
        extract_amenity_features(t, d) 
        for t, d in zip(df_valid["title"], df_valid["short_description"])
    ]
    df_amenities = pd.DataFrame(amenity_records)
    for col in df_amenities.columns:
        df_valid[col] = df_amenities[col].values

    # 6. Geospatial Coordinates & Distance Calculations
    df_valid["latitude"] = pd.to_numeric(df_valid["latitude"], errors="coerce")
    df_valid["longitude"] = pd.to_numeric(df_valid["longitude"], errors="coerce")
    
    if "city_default_lat" in df_valid.columns and "city_default_lon" in df_valid.columns:
        df_valid["latitude"] = df_valid["latitude"].fillna(df_valid["city_default_lat"])
        df_valid["longitude"] = df_valid["longitude"].fillna(df_valid["city_default_lon"])
    else:
        df_valid["latitude"] = df_valid["latitude"].fillna(-6.2088)
        df_valid["longitude"] = df_valid["longitude"].fillna(106.8200)

    # Distance to Jakarta Prime CBD
    cbd_lat, cbd_lon = JAKARTA_CBD_COORDS
    df_valid["distance_to_cbd_km"] = [
        haversine_distance_km(lat, lon, cbd_lat, cbd_lon)
        for lat, lon in zip(df_valid["latitude"], df_valid["longitude"])
    ]

    # Distance to nearest transit node
    nearest_transit_dist = []
    nearest_transit_name = []
    for lat, lon in zip(df_valid["latitude"], df_valid["longitude"]):
        dists = {name: haversine_distance_km(lat, lon, t_lat, t_lon) for name, (t_lat, t_lon) in KEY_TRANSIT_HUBS.items()}
        closest = min(dists, key=dists.get)
        nearest_transit_name.append(closest)
        nearest_transit_dist.append(dists[closest])

    df_valid["nearest_transit_hub"] = nearest_transit_name
    df_valid["distance_to_transit_km"] = nearest_transit_dist

    # Cluster Zone Definition
    def assign_urban_zone(cbd_dist: float) -> str:
        if cbd_dist <= 7.0:
            return "Tier 1: Core Urban Center (<7km)"
        elif cbd_dist <= 15.0:
            return "Tier 2: Inner Ring Metro (7-15km)"
        elif cbd_dist <= 28.0:
            return "Tier 3: Outer Commuter Ring (15-28km)"
        else:
            return "Tier 4: Greater Satellite Periphery (>28km)"

    df_valid["urban_zone"] = df_valid["distance_to_cbd_km"].apply(assign_urban_zone)

    # 7. Normalize Location Attributes
    def extract_subdistrict(row):
        loc = str(row["display_location"]).strip()
        parts = [p.strip() for p in loc.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[0]
        return row["target_city"]

    df_valid["subdistrict"] = df_valid.apply(extract_subdistrict, axis=1)
    
    # Assign unique surrogate ID
    df_valid["listing_id"] = [f"LST-{i+1:05d}" for i in range(len(df_valid))]

    ordered_cols = [
        "listing_id", "title", "url", "target_city", "target_province", "subdistrict",
        "display_location", "property_type", "price_monthly_idr", "price_per_m2_idr",
        "original_period", "bedrooms", "bathrooms", "layout_category", "floor_size_m2",
        "distance_to_cbd_km", "distance_to_transit_km", "nearest_transit_hub", "urban_zone",
        "is_full_furnished", "is_semi_furnished", "is_unfurnished",
        "has_ac", "has_wifi", "has_water_heater", "has_pool", "has_gym", "near_transit",
        "has_balcony", "has_kitchen", "has_parking",
        "latitude", "longitude", "image_url", "short_description"
    ]
    df_final = df_valid[ordered_cols].copy()

    clean_csv_path = os.path.join(output_dir, "jabodetabek_rental_cleaned.csv")
    df_final.to_csv(clean_csv_path, index=False, encoding="utf-8")
    logger.info(f"Transformation complete! Saved {len(df_final)} clean records to {clean_csv_path}")

    return df_final


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(base_dir, "data", "raw", "raw_rental_listings_staged.json")
    out_dir = os.path.join(base_dir, "data", "processed")
    clean_and_transform_pipeline(raw_path, out_dir)