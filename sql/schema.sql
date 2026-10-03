-- =====================================================================
-- Star Schema & Analytical Views for Greater Jakarta Rental Housing
-- Database: rental_intelligence.db (SQLite / PostgreSQL Compatible)
-- Fact: fact_rental_listings
-- Dimensions: dim_locations, dim_specifications
-- =====================================================================

DROP TABLE IF EXISTS fact_rental_listings;
DROP TABLE IF EXISTS dim_locations;
DROP TABLE IF EXISTS dim_specifications;

-- 1. Locations Dimension
CREATE TABLE dim_locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name TEXT NOT NULL,
    province TEXT NOT NULL,
    subdistrict TEXT,
    avg_city_tier TEXT
);

-- 2. Property Specifications & Amenities Dimension
CREATE TABLE dim_specifications (
    spec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bedrooms INTEGER,
    bathrooms INTEGER,
    floor_size_m2 REAL,
    is_full_furnished INTEGER,
    is_semi_furnished INTEGER,
    is_unfurnished INTEGER,
    has_ac INTEGER,
    has_wifi INTEGER,
    has_water_heater INTEGER,
    has_pool INTEGER,
    near_transit INTEGER,
    has_balcony INTEGER
);

-- 3. Core Fact Table
CREATE TABLE fact_rental_listings (
    listing_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT,
    city_name TEXT NOT NULL,
    subdistrict TEXT,
    province TEXT NOT NULL,
    price_monthly_idr REAL NOT NULL,
    price_per_m2_idr REAL NOT NULL,
    original_period TEXT,
    bedrooms INTEGER,
    bathrooms INTEGER,
    floor_size_m2 REAL,
    is_full_furnished INTEGER,
    is_semi_furnished INTEGER,
    is_unfurnished INTEGER,
    has_ac INTEGER,
    has_wifi INTEGER,
    has_water_heater INTEGER,
    has_pool INTEGER,
    near_transit INTEGER,
    has_balcony INTEGER,
    latitude REAL,
    longitude REAL,
    estimated_fair_price REAL,
    undervalued_discount_pct REAL,
    valuation_status TEXT
);

-- =====================================================================
-- Analytical SQL Views for Market Intelligence
-- =====================================================================

DROP VIEW IF EXISTS view_city_rental_benchmarks;
DROP VIEW IF EXISTS view_bedroom_rental_pricing;
DROP VIEW IF EXISTS view_top_undervalued_deals;
DROP VIEW IF EXISTS view_amenity_rental_premium;

-- View 1: City Benchmarks & Affordability Ranking
CREATE VIEW view_city_rental_benchmarks AS
SELECT
    city_name,
    province,
    COUNT(listing_id) AS total_active_listings,
    ROUND(AVG(price_monthly_idr), 0) AS mean_monthly_rent_idr,
    ROUND(AVG(price_per_m2_idr), 0) AS mean_price_per_m2_idr,
    ROUND(AVG(floor_size_m2), 1) AS avg_floor_size_m2,
    MIN(price_monthly_idr) AS min_monthly_rent_idr,
    MAX(price_monthly_idr) AS max_monthly_rent_idr
FROM fact_rental_listings
GROUP BY city_name, province
ORDER BY mean_price_per_m2_idr DESC;

-- View 2: Bedroom Layout Price Distribution
CREATE VIEW view_bedroom_rental_pricing AS
SELECT
    CASE 
        WHEN bedrooms = 1 THEN '1 BR / Studio'
        WHEN bedrooms = 2 THEN '2 BR'
        WHEN bedrooms = 3 THEN '3 BR'
        ELSE '4+ BR / Penthouse'
    END AS layout_category,
    COUNT(listing_id) AS listing_count,
    ROUND(AVG(floor_size_m2), 1) AS avg_area_m2,
    ROUND(AVG(price_monthly_idr), 0) AS avg_monthly_rent_idr,
    ROUND(AVG(price_per_m2_idr), 0) AS avg_price_per_m2_idr
FROM fact_rental_listings
GROUP BY layout_category
ORDER BY avg_monthly_rent_idr ASC;

-- View 3: Undervalued "Good Deal" Radar
CREATE VIEW view_top_undervalued_deals AS
SELECT
    listing_id,
    title,
    city_name,
    subdistrict,
    bedrooms,
    floor_size_m2,
    ROUND(price_monthly_idr, 0) AS actual_monthly_rent_idr,
    ROUND(estimated_fair_price, 0) AS estimated_fair_price_idr,
    ROUND(undervalued_discount_pct, 1) AS discount_vs_market_pct,
    valuation_status,
    url
FROM fact_rental_listings
WHERE valuation_status IN ('High Value Deal (>25% Discount)', 'Fair Value Deal (10-25% Discount)')
ORDER BY undervalued_discount_pct DESC;

-- View 4: Furnishing & Amenity Premium Evaluation
CREATE VIEW view_amenity_rental_premium AS
SELECT
    CASE 
        WHEN is_full_furnished = 1 THEN 'Full Furnished'
        WHEN is_semi_furnished = 1 THEN 'Semi Furnished'
        ELSE 'Unfurnished / Bare'
    END AS furnishing_status,
    COUNT(listing_id) AS total_units,
    ROUND(AVG(price_per_m2_idr), 0) AS avg_price_per_m2_idr,
    ROUND(AVG(price_monthly_idr), 0) AS avg_monthly_rent_idr
FROM fact_rental_listings
GROUP BY furnishing_status
ORDER BY avg_price_per_m2_idr DESC;
