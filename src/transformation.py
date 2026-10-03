"""
transformation.py
Data Cleaning, Normalization, & Feature Engineering Pipeline.
Transforms staged raw JSON listings into normalized relational-ready tabular data.
"""

import os
import sys
import re
import json
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def parse_normalized_price(raw_val: str) -> Tuple[float, str, bool]:
    """
    Parses Indonesian price string and converts to standardized monthly rent in IDR.
    Detects ad listings with sale prices (Miliar) that do not belong to rental.
    """
    if not isinstance(raw_val, str) or not raw_val.strip():
        return np.nan, "unknown", False

    s = raw_val.lower().replace("rp", "").strip()
    
    # Flag primary property development sales ads mistakenly in rental feed
    if "miliar" in s or " m " in f" {s} ":
        # If it explicitly says "per tahun" or "per bulan", it's a luxury rental, else likely sale price
        if not ("tahun" in s or "bulan" in s):
            return np.nan, "sale_outlier", True

    is_yearly = "/tahun" in s or "tahun" in s
    is_daily = "/hari" in s or "hari" in s
    is_monthly = "/bulan" in s or "bulan" in s or (not is_yearly and not is_daily)

    # Clean text to extract numeric part
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

    # Convert to monthly equivalent
    if is_yearly:
        monthly_price = num / 12.0
        period = "yearly"
    elif is_daily:
        monthly_price = num * 30.0
        period = "daily"
    else:
        monthly_price = num
        period = "monthly"

    # Extreme filter: rental apartemen jabodetabek realistic monthly range (Rp 800k - Rp 150 Jt/bln)
    is_outlier = (monthly_price < 500_000) or (monthly_price > 200_000_000)
    return monthly_price, period, is_outlier


def extract_amenity_features(title: str, desc: str) -> Dict[str, int]:
    """
    NLP keyword extraction for apartment amenities from Indonesian property descriptions.
    """
    combined_text = f"{str(title).lower()} {str(desc).lower()}"
    
    # 1. Furnishing status
    is_full_furnished = int(bool(re.search(r'\bfull(?:y)?\s*(?:furnished|furnish)\b|\bfff\b', combined_text)))
    is_semi_furnished = int(bool(re.search(r'\bsemi\s*(?:furnished|furnish)\b', combined_text)))
    is_unfurnished = int(bool(re.search(r'\bunfurnished|non\s*furnish|kosong\b', combined_text)))
    
    # 2. AC presence
    has_ac = int(bool(re.search(r'\bac\b|air\s*conditioner', combined_text)))
    
    # 3. WiFi / Internet
    has_wifi = int(bool(re.search(r'\bwifi\b|internet|indihome|biznet', combined_text)))
    
    # 4. Water heater
    has_water_heater = int(bool(re.search(r'\bwater\s*heater|pemanas\s*air\b', combined_text)))
    
    # 5. Swimming pool / gym facility
    has_pool = int(bool(re.search(r'\bkolam\s*renang|swimming\s*pool|gym|fitness\b', combined_text)))
    
    # 6. Proximity to transit (MRT / LRT / KRL / Stasiun)
    near_transit = int(bool(re.search(r'\bmrt\b|\blrt\b|\bkrl\b|\bstasiun\b|\btransjakarta\b|\bbusway\b', combined_text)))
    
    # 7. Balcony
    has_balcony = int(bool(re.search(r'\bbalcon|balkon\b', combined_text)))

    return {
        "is_full_furnished": is_full_furnished,
        "is_semi_furnished": is_semi_furnished,
        "is_unfurnished": is_unfurnished,
        "has_ac": has_ac,
        "has_wifi": has_wifi,
        "has_water_heater": has_water_heater,
        "has_pool": has_pool,
        "near_transit": near_transit,
        "has_balcony": has_balcony
    }


def clean_and_transform_pipeline(raw_json_path: str, output_dir: str = "data/processed") -> pd.DataFrame:
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Loading raw staged JSON from {raw_json_path}...")
    
    with open(raw_json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    df = pd.DataFrame(raw_data)
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} raw records.")

    # 1. Deduplication on URL and (Title + Location)
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
    
    # Impute missing floor size by median of same bedroom count in same city
    df_valid["floor_size_m2"] = pd.to_numeric(df_valid["floor_size_m2"], errors="coerce")
    median_by_br = df_valid.groupby("bedrooms")["floor_size_m2"].transform("median")
    df_valid["floor_size_m2"] = df_valid["floor_size_m2"].fillna(median_by_br).fillna(36.0)
    
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

    # 6. Normalize Location Attributes
    # Extract subdistrict (kecamatan) if present in display_location
    def extract_subdistrict(row):
        loc = str(row["display_location"]).strip()
        parts = [p.strip() for p in loc.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[0]
        return row["target_city"]

    df_valid["subdistrict"] = df_valid.apply(extract_subdistrict, axis=1)
    
    # Clean unique listing ID
    df_valid["listing_id"] = [f"LST-{i+1:05d}" for i in range(len(df_valid))]

    # Select and order final cleaned columns
    ordered_cols = [
        "listing_id", "title", "url", "target_city", "target_province", "subdistrict",
        "display_location", "property_type", "price_monthly_idr", "price_per_m2_idr",
        "original_period", "bedrooms", "bathrooms", "floor_size_m2",
        "is_full_furnished", "is_semi_furnished", "is_unfurnished",
        "has_ac", "has_wifi", "has_water_heater", "has_pool", "near_transit", "has_balcony",
        "latitude", "longitude", "image_url", "short_description"
    ]
    df_final = df_valid[ordered_cols].copy()

    # Save to clean CSV
    clean_csv_path = os.path.join(output_dir, "jabodetabek_rental_cleaned.csv")
    df_final.to_csv(clean_csv_path, index=False, encoding="utf-8")
    logger.info(f"Transformation complete! Saved {len(df_final)} clean records to {clean_csv_path}")

    return df_final


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(base_dir, "data", "raw", "raw_rental_listings_staged.json")
    out_dir = os.path.join(base_dir, "data", "processed")
    clean_and_transform_pipeline(raw_path, out_dir)
