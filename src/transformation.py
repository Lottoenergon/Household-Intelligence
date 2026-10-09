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


# Bounding box Jabodetabek (WGS84). Koordinat di luar kotak ini dianggap tidak valid.
JABODETABEK_BBOX = {"lat_min": -6.80, "lat_max": -5.95, "lon_min": 106.35, "lon_max": 107.25}
MIN_LISTINGS_FOR_SUBDISTRICT_CENTROID = 2


def is_valid_jabodetabek_coord(lat: float, lon: float) -> bool:
    """True jika koordinat ada, bukan NaN, dan berada di dalam bounding box Jabodetabek.

    Otomatis menolak kasus portal di mana longitude tersalin dari latitude
    (misal -6.23168, -6.23168), karena nilai itu jatuh di luar bounding box.
    """
    if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
        return False
    b = JABODETABEK_BBOX
    return (b["lat_min"] <= lat <= b["lat_max"]) and (b["lon_min"] <= lon <= b["lon_max"])


def clean_and_impute_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Validasi koordinat lalu imputasi yang hilang/rusak TANPA memakai titik CBD.

    Urutan imputasi:
      1. koordinat listing asli (jika valid)          -> geo_source = "listing"
      2. median koordinat valid se-subdistrik         -> geo_source = "subdistrict_centroid"
      3. median koordinat valid se-kota               -> geo_source = "city_centroid"
    Butuh kolom: latitude, longitude, subdistrict, target_city.
    """
    out = df.copy()
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce")

    valid = pd.Series(
        [is_valid_jabodetabek_coord(a, b) for a, b in zip(out["latitude"], out["longitude"])],
        index=out.index,
    )
    out["geo_source"] = np.where(valid, "listing", "missing")
    out.loc[~valid, ["latitude", "longitude"]] = np.nan

    good = out[valid]
    sub_stats = good.groupby(["target_city", "subdistrict"])[["latitude", "longitude"]].agg(["median", "count"])
    city_stats = good.groupby("target_city")[["latitude", "longitude"]].median()

    for idx in out.index[~valid]:
        city, sub = out.at[idx, "target_city"], out.at[idx, "subdistrict"]
        key = (city, sub)
        if key in sub_stats.index and sub_stats.loc[key, ("latitude", "count")] >= MIN_LISTINGS_FOR_SUBDISTRICT_CENTROID:
            out.at[idx, "latitude"] = sub_stats.loc[key, ("latitude", "median")]
            out.at[idx, "longitude"] = sub_stats.loc[key, ("longitude", "median")]
            out.at[idx, "geo_source"] = "subdistrict_centroid"
        elif city in city_stats.index:
            out.at[idx, "latitude"] = city_stats.at[city, "latitude"]
            out.at[idx, "longitude"] = city_stats.at[city, "longitude"]
            out.at[idx, "geo_source"] = "city_centroid"
        # jika kota pun tidak punya koordinat valid, biarkan NaN (jangan dikarang)

    out["geo_is_imputed"] = (out["geo_source"] != "listing").astype(int)
    return out


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


def extract_amenity_features(title: str, desc: str, extra: str = "") -> Dict[str, int]:
    """
    NLP keyword extraction for apartment amenities from Indonesian property descriptions.
    extra: additional text (e.g., top_facility from Mamikos) to boost signal for sources with thin descriptions.
    """
    combined_text = f"{str(title).lower()} {str(desc).lower()} {str(extra).lower()}"
    
    # 1. Furnishing status (also check furnished_status field passed via extra)
    is_full_furnished = int(bool(re.search(r'\bfull(?:y)?\s*(?:furnished|furnish)|\bfff\b', combined_text)))
    is_semi_furnished = int(bool(re.search(r'\bsemi\s*(?:furnished|furnish)\b', combined_text)))
    is_unfurnished = int(bool(re.search(r'\bunfurnished|\bnon\s*furnish|\bkosongan?\b', combined_text)))
    
    # 2. Specific Amenities - expanded for Mamikos top_facility values
    # AC variants: "AC", "Air Conditioner", "air conditioner"
    has_ac = int(bool(re.search(r'\bac\b|air\s*conditioner', combined_text)))
    # WiFi variants: "WiFi", "internet", "indihome", "biznet"
    has_wifi = int(bool(re.search(r'\bwifi\b|internet|indihome|biznet', combined_text)))
    has_water_heater = int(bool(re.search(r'water\s*heater|pemanas\s*air', combined_text)))
    # Pool: "kolam renang", "swimming pool", "pool"
    has_pool = int(bool(re.search(r'kolam\s*renang|swimming\s*pool|\bpool\b', combined_text)))
    # Gym: "gym", "fitness", "pusat kebugaran" - Mamikos doesn't have this explicitly
    has_gym = int(bool(re.search(r'\bgym\b|fitness|pusat\s*kebugaran', combined_text)))
    # Balcony: "balcon", "balkon"
    has_balcony = int(bool(re.search(r'balcon|balkon', combined_text)))
    # Kitchen: "kitchen set", "dapur", "kompor"
    has_kitchen = int(bool(re.search(r'kitchen\s*set|dapur|kompor', combined_text)))
    # Transit: "mrt", "lrt", "krl", "stasiun", "transjakarta", "busway"
    near_transit = int(bool(re.search(r'\bmrt\b|\blrt\b|\bkrl\b|\bstasiun\b|\btransjakarta\b|\bbusway\b', combined_text)))
    # Parking: "parkir", "parking"
    has_parking = int(bool(re.search(r'parkir|parking', combined_text)))
    # Mamikos-specific from top_facility: "K. Mandi Dalam" = kamar mandi dalam (implied by bathroom count), 
    # "Kloset Duduk" = toilet, "Akses 24 Jam" = 24h access, "Kasur" = bed (furnished signal)

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


CONTENT_DUP_KEY = ["price_monthly_idr", "floor_size_m2", "bedrooms", "bathrooms", "display_location"]


def drop_content_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Buang listing kembar antar-broker: harga, luas, kamar, kamar mandi, dan lokasi sama persis.

    Dedup URL saja tidak cukup karena satu unit sering diiklankan beberapa broker dengan URL berbeda.
    Listing pertama dipertahankan. Kolom NaN diperlakukan sama (luas kosong + atribut lain sama = kembar).
    Risiko yang diterima: dua unit berbeda dengan spesifikasi identik di gedung yang sama ikut terbuang.
    """
    before = len(df)
    out = df.drop_duplicates(subset=CONTENT_DUP_KEY, keep="first").reset_index(drop=True)
    return out, before - len(out)


def clean_and_transform_pipeline(raw_json_path: str, output_dir: str = "data/processed") -> pd.DataFrame:
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Loading raw staged JSON from {raw_json_path}...")
    
    with open(raw_json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    df = pd.DataFrame(raw_data)
    initial_count = len(df)
    audit = {"raw_records": int(initial_count)}
    logger.info(f"Loaded {initial_count} raw records.")

    # 1. Deduplication on URL and title
    df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)
    logger.info(f"Deduplicated by URL: {len(df)} remaining (-{initial_count - len(df)} duplicates).")
    audit["after_url_dedup"] = int(len(df))

    # 2. Parse price & rental duration
    price_res = [parse_normalized_price(p) for p in df["raw_price"]]
    df["price_monthly_idr"] = [r[0] for r in price_res]
    df["original_period"] = [r[1] for r in price_res]
    df["is_price_outlier"] = [r[2] for r in price_res]

    # Filter out invalid prices and sale outliers
    valid_mask = df["price_monthly_idr"].notnull() & (~df["is_price_outlier"])
    df_valid = df[valid_mask].copy().reset_index(drop=True)
    logger.info(f"Price validation complete: {len(df_valid)} valid rentals remaining (-{len(df) - len(df_valid)} outliers/ads).")
    audit["after_price_validation"] = int(len(df_valid))
    audit["price_period_counts"] = {k: int(v) for k, v in df_valid["original_period"].value_counts().items()}

    # 3. Clean numeric fields (bedrooms, bathrooms, floor_size)
    df_valid["bedrooms"] = pd.to_numeric(df_valid["bedrooms"], errors="coerce").fillna(1).astype(int)
    df_valid["bathrooms"] = pd.to_numeric(df_valid["bathrooms"], errors="coerce").fillna(1).astype(int)
    
    # 3b. Dedup berbasis konten (sebelum imputasi luas, agar median imputasi tidak terdistorsi duplikat)
    df_valid, n_content_dups = drop_content_duplicates(df_valid)
    logger.info(f"Content-based dedup: {len(df_valid)} remaining (-{n_content_dups} duplikat lintas-broker).")
    audit["content_duplicates_removed"] = int(n_content_dups)
    audit["after_content_dedup"] = int(len(df_valid))

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
    audit["floor_size_missing_imputed"] = int(df_valid["floor_size_m2"].isna().sum())
    median_by_br = df_valid.groupby(["target_city", "bedrooms"])["floor_size_m2"].transform("median")
    fallback_median = df_valid.groupby("bedrooms")["floor_size_m2"].transform("median")
    df_valid["floor_size_m2"] = df_valid["floor_size_m2"].fillna(median_by_br).fillna(fallback_median).fillna(36.0)
    
    # Floor size realistic bounds (15 m2 studio to 350 m2 penthouse)
    df_valid = df_valid[(df_valid["floor_size_m2"] >= 15) & (df_valid["floor_size_m2"] <= 350)].copy()

    audit["after_floor_bounds"] = int(len(df_valid))

    # 4. Calculate Price per m2 (Key Real Estate Metric)
    df_valid["price_per_m2_idr"] = df_valid["price_monthly_idr"] / df_valid["floor_size_m2"]

    # 5. Extract NLP amenity vectors
    # `extra` mengangkat sinyal dari field sumber yang tidak masuk title/description
    # (Mamikos: top_facility, furnished_status, unit_type) supaya source dengan
    # deskripsi tipis tetap punya vektor amenity yang tidak nol.
    def _build_amenity_extra(row):
        parts = []
        for col in ("top_facility", "furnished_status", "unit_type", "area_label"):
            val = row.get(col)
            if isinstance(val, str) and val.strip():
                parts.append(val)
            elif isinstance(val, list):
                parts.extend([str(v) for v in val if v])
        return " ".join(parts)

    amenity_records = [
        extract_amenity_features(t, d, _build_amenity_extra(row))
        for (t, d), (_, row) in zip(
            zip(df_valid["title"], df_valid["short_description"]),
            df_valid.iterrows(),
        )
    ]
    df_amenities = pd.DataFrame(amenity_records)
    for col in df_amenities.columns:
        df_valid[col] = df_amenities[col].values

    # 6. Geospatial: subdistrik dulu (dibutuhkan untuk imputasi centroid), lalu validasi koordinat
    def extract_subdistrict(row):
        loc = str(row["display_location"]).strip()
        parts = [p.strip() for p in loc.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[0]
        return row["target_city"]

    df_valid["subdistrict"] = df_valid.apply(extract_subdistrict, axis=1)

    n_before = int(df_valid[["latitude", "longitude"]].apply(pd.to_numeric, errors="coerce").isna().any(axis=1).sum())
    df_valid = clean_and_impute_coordinates(df_valid)
    src_counts = df_valid["geo_source"].value_counts().to_dict()
    logger.info(f"Geo cleaning: {n_before} koordinat kosong di sumber; hasil geo_source = {src_counts}")
    df_valid = df_valid.dropna(subset=["latitude", "longitude"]).copy()
    audit["geo_source_counts"] = {k: int(v) for k, v in src_counts.items()}

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
        "latitude", "longitude", "geo_source", "geo_is_imputed", "image_url", "short_description"
    ]
    df_final = df_valid[ordered_cols].copy()

    clean_csv_path = os.path.join(output_dir, "jabodetabek_rental_cleaned.csv")
    df_final.to_csv(clean_csv_path, index=False, encoding="utf-8")
    logger.info(f"Transformation complete! Saved {len(df_final)} clean records to {clean_csv_path}")

    audit["final_records"] = int(len(df_final))
    audit["geo_imputed_share_by_city"] = {k: round(float(v), 4) for k, v in df_final.groupby("target_city")["geo_is_imputed"].mean().items()}
    with open(os.path.join(output_dir, "pipeline_audit.json"), "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    return df_final


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(base_dir, "data", "raw", "raw_rental_listings_staged.json")
    out_dir = os.path.join(base_dir, "data", "processed")
    clean_and_transform_pipeline(raw_path, out_dir)