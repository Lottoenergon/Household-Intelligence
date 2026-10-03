-- =====================================================================
-- Star Schema & Analytical Views for Greater Jakarta Rental Housing
-- Database: rental_intelligence.db (SQLite / PostgreSQL Compatible)
-- Analytics Stack: Fact Listings + Location / Spec / Amenity Dimensions
-- =====================================================================

DROP TABLE IF EXISTS fact_rental_listings;
DROP TABLE IF EXISTS dim_locations;
DROP TABLE IF EXISTS dim_property_specs;
DROP TABLE IF EXISTS dim_amenities;

-- 1. Dimension: Locations & Geospatial Metrics
CREATE TABLE dim_locations (
    location_key INTEGER PRIMARY KEY AUTOINCREMENT,
    subdistrict TEXT,
    target_city TEXT,
    target_province TEXT,
    urban_zone TEXT,
    latitude REAL,
    longitude REAL,
    distance_to_cbd_km REAL,
    nearest_transit_hub TEXT,
    distance_to_transit_km REAL
);

-- 2. Dimension: Property Physical Specifications
CREATE TABLE dim_property_specs (
    spec_key INTEGER PRIMARY KEY AUTOINCREMENT,
    property_type TEXT,
    bedrooms INTEGER,
    bathrooms INTEGER,
    layout_category TEXT,
    floor_size_m2 REAL
);

-- 3. Dimension: Amenities & Interior Furnishing
CREATE TABLE dim_amenities (
    amenity_key INTEGER PRIMARY KEY AUTOINCREMENT,
    is_full_furnished INTEGER,
    is_semi_furnished INTEGER,
    is_unfurnished INTEGER,
    has_ac INTEGER,
    has_wifi INTEGER,
    has_water_heater INTEGER,
    has_pool INTEGER,
    has_gym INTEGER,
    has_balcony INTEGER,
    has_kitchen INTEGER,
    near_transit INTEGER,
    has_parking INTEGER
);

-- 4. Fact Table: Rental Listings & Econometric Valuation
CREATE TABLE fact_rental_listings (
    listing_key INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT UNIQUE,
    location_key INTEGER,
    spec_key INTEGER,
    amenity_key INTEGER,
    title TEXT,
    url TEXT,
    price_monthly_idr REAL,
    price_per_m2_idr REAL,
    original_period TEXT,
    fair_market_rent_idr REAL,
    residual_idr REAL,
    discount_pct REAL,
    deal_score_z REAL,
    deal_classification TEXT,
    image_url TEXT,
    short_description TEXT,
    FOREIGN KEY (location_key) REFERENCES dim_locations(location_key),
    FOREIGN KEY (spec_key) REFERENCES dim_property_specs(spec_key),
    FOREIGN KEY (amenity_key) REFERENCES dim_amenities(amenity_key)
);

-- =====================================================================
-- Analytical SQL Views for Market Intelligence
-- =====================================================================

DROP VIEW IF EXISTS view_city_market_benchmarks;
DROP VIEW IF EXISTS view_urban_zone_distance_decay;
DROP VIEW IF EXISTS view_transit_proximity_premium;
DROP VIEW IF EXISTS view_layout_and_bedroom_matrix;
DROP VIEW IF EXISTS view_top_undervalued_deals;
DROP VIEW IF EXISTS view_amenity_hedonic_premiums;

-- View 1: City Market Benchmarks
CREATE VIEW view_city_market_benchmarks AS
SELECT
    l.target_city,
    COUNT(f.listing_key) AS total_inventory,
    ROUND(AVG(f.price_monthly_idr), 0) AS mean_monthly_rent_idr,
    ROUND(AVG(f.price_per_m2_idr), 0) AS mean_price_per_m2_idr,
    ROUND(AVG(s.floor_size_m2), 1) AS avg_floor_size_m2,
    ROUND(AVG(l.distance_to_cbd_km), 1) AS avg_dist_to_cbd_km,
    ROUND(SUM(a.is_full_furnished) * 100.0 / COUNT(f.listing_key), 1) AS pct_full_furnished,
    ROUND(SUM(a.has_pool) * 100.0 / COUNT(f.listing_key), 1) AS pct_with_pool
FROM fact_rental_listings f
JOIN dim_locations l ON f.location_key = l.location_key
JOIN dim_property_specs s ON f.spec_key = s.spec_key
JOIN dim_amenities a ON f.amenity_key = a.amenity_key
GROUP BY l.target_city
ORDER BY mean_price_per_m2_idr DESC;

-- View 2: Urban Zone Distance Decay (CBD Spatial Gradient)
CREATE VIEW view_urban_zone_distance_decay AS
SELECT
    l.urban_zone,
    COUNT(f.listing_key) AS sample_size,
    ROUND(AVG(l.distance_to_cbd_km), 1) AS avg_cbd_dist_km,
    ROUND(AVG(f.price_monthly_idr), 0) AS avg_monthly_rent_idr,
    ROUND(AVG(f.price_per_m2_idr), 0) AS avg_price_per_m2_idr,
    ROUND(AVG(s.floor_size_m2), 1) AS avg_unit_size_m2
FROM fact_rental_listings f
JOIN dim_locations l ON f.location_key = l.location_key
JOIN dim_property_specs s ON f.spec_key = s.spec_key
GROUP BY l.urban_zone
ORDER BY avg_cbd_dist_km ASC;

-- View 3: Transit Proximity Premium (KRL / MRT / LRT Accessibility)
CREATE VIEW view_transit_proximity_premium AS
SELECT
    CASE
        WHEN l.distance_to_transit_km <= 2.0 THEN 'Walking / First-Mile (<2km)'
        WHEN l.distance_to_transit_km <= 5.0 THEN 'Feeder Transit Range (2-5km)'
        ELSE 'Car / Commuter Reliant (>5km)'
    END AS transit_accessibility_tier,
    COUNT(f.listing_key) AS listing_count,
    ROUND(AVG(l.distance_to_transit_km), 2) AS avg_transit_distance_km,
    ROUND(AVG(f.price_per_m2_idr), 0) AS avg_price_per_m2_idr,
    ROUND(AVG(f.price_monthly_idr), 0) AS avg_monthly_rent_idr
FROM fact_rental_listings f
JOIN dim_locations l ON f.location_key = l.location_key
GROUP BY transit_accessibility_tier
ORDER BY avg_transit_distance_km ASC;

-- View 4: Bedroom & Layout Classification Matrix
CREATE VIEW view_layout_and_bedroom_matrix AS
SELECT
    s.layout_category,
    s.bedrooms,
    COUNT(f.listing_key) AS total_units,
    ROUND(AVG(s.floor_size_m2), 1) AS avg_size_m2,
    ROUND(MIN(f.price_monthly_idr), 0) AS min_monthly_rent_idr,
    ROUND(AVG(f.price_monthly_idr), 0) AS avg_monthly_rent_idr,
    ROUND(MAX(f.price_monthly_idr), 0) AS max_monthly_rent_idr,
    ROUND(AVG(f.price_per_m2_idr), 0) AS avg_price_per_m2_idr
FROM fact_rental_listings f
JOIN dim_property_specs s ON f.spec_key = s.spec_key
GROUP BY s.layout_category, s.bedrooms
ORDER BY s.bedrooms ASC;

-- View 5: Top Undervalued Deals (Deal Hunter Radar)
CREATE VIEW view_top_undervalued_deals AS
SELECT
    f.listing_id,
    f.title,
    l.target_city,
    l.subdistrict,
    s.layout_category,
    s.floor_size_m2,
    ROUND(f.price_monthly_idr, 0) AS actual_rent_idr,
    ROUND(f.fair_market_rent_idr, 0) AS fair_market_rent_idr,
    ROUND(f.residual_idr, 0) AS monthly_discount_idr,
    f.discount_pct,
    ROUND(f.deal_score_z, 2) AS deal_z_score,
    f.deal_classification,
    f.url
FROM fact_rental_listings f
JOIN dim_locations l ON f.location_key = l.location_key
JOIN dim_property_specs s ON f.spec_key = s.spec_key
WHERE f.deal_score_z <= -1.0
ORDER BY f.deal_score_z ASC;

-- View 6: Furnishing & Amenity Premiums
CREATE VIEW view_amenity_hedonic_premiums AS
SELECT
    'Full Furnished vs Unfurnished' AS feature_contrast,
    ROUND(AVG(CASE WHEN a.is_full_furnished = 1 THEN f.price_per_m2_idr END), 0) AS with_feature_price_m2,
    ROUND(AVG(CASE WHEN a.is_full_furnished = 0 THEN f.price_per_m2_idr END), 0) AS without_feature_price_m2,
    ROUND(
        (AVG(CASE WHEN a.is_full_furnished = 1 THEN f.price_per_m2_idr END) - 
         AVG(CASE WHEN a.is_full_furnished = 0 THEN f.price_per_m2_idr END)) * 100.0 /
        AVG(CASE WHEN a.is_full_furnished = 0 THEN f.price_per_m2_idr END), 1
    ) AS premium_pct
FROM fact_rental_listings f
JOIN dim_amenities a ON f.amenity_key = a.amenity_key
UNION ALL
SELECT
    'Swimming Pool Access' AS feature_contrast,
    ROUND(AVG(CASE WHEN a.has_pool = 1 THEN f.price_per_m2_idr END), 0) AS with_feature_price_m2,
    ROUND(AVG(CASE WHEN a.has_pool = 0 THEN f.price_per_m2_idr END), 0) AS without_feature_price_m2,
    ROUND(
        (AVG(CASE WHEN a.has_pool = 1 THEN f.price_per_m2_idr END) - 
         AVG(CASE WHEN a.has_pool = 0 THEN f.price_per_m2_idr END)) * 100.0 /
        AVG(CASE WHEN a.has_pool = 0 THEN f.price_per_m2_idr END), 1
    ) AS premium_pct
FROM fact_rental_listings f
JOIN dim_amenities a ON f.amenity_key = a.amenity_key
UNION ALL
SELECT
    'Air Conditioning (AC) Unit' AS feature_contrast,
    ROUND(AVG(CASE WHEN a.has_ac = 1 THEN f.price_per_m2_idr END), 0) AS with_feature_price_m2,
    ROUND(AVG(CASE WHEN a.has_ac = 0 THEN f.price_per_m2_idr END), 0) AS without_feature_price_m2,
    ROUND(
        (AVG(CASE WHEN a.has_ac = 1 THEN f.price_per_m2_idr END) - 
         AVG(CASE WHEN a.has_ac = 0 THEN f.price_per_m2_idr END)) * 100.0 /
        AVG(CASE WHEN a.has_ac = 0 THEN f.price_per_m2_idr END), 1
    ) AS premium_pct
FROM fact_rental_listings f
JOIN dim_amenities a ON f.amenity_key = a.amenity_key;