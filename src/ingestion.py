"""
ingestion.py
Data Ingestion Engine for Jabodetabek Rental Housing Intelligence.
Extracts public rental apartment listings across Greater Jakarta (Jabodetabek)
with rate-limiting, error recovery, schema validation, and raw staging.
"""

import os
import sys
import time
import json
import random
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

TARGET_REGIONS = [
    {"region_slug": "jakarta-selatan", "city_name": "Jakarta Selatan", "province": "DKI Jakarta"},
    {"region_slug": "jakarta-pusat", "city_name": "Jakarta Pusat", "province": "DKI Jakarta"},
    {"region_slug": "jakarta-barat", "city_name": "Jakarta Barat", "province": "DKI Jakarta"},
    {"region_slug": "jakarta-timur", "city_name": "Jakarta Timur", "province": "DKI Jakarta"},
    {"region_slug": "jakarta-utara", "city_name": "Jakarta Utara", "province": "DKI Jakarta"},
    {"region_slug": "tangerang", "city_name": "Tangerang", "province": "Banten"},
    {"region_slug": "tangerang-selatan", "city_name": "Tangerang Selatan", "province": "Banten"},
    {"region_slug": "depok", "city_name": "Depok", "province": "Jawa Barat"},
    {"region_slug": "bekasi", "city_name": "Bekasi", "province": "Jawa Barat"},
    {"region_slug": "bogor", "city_name": "Bogor", "province": "Jawa Barat"}
]


def fetch_page_with_retry(url: str, max_retries: int = 3, backoff_base: float = 1.5) -> Optional[str]:
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive"
    }
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 429:
                sleep_sec = backoff_base ** attempt + random.uniform(1.0, 3.0)
                logger.warning(f"Rate limited (429) at {url}. Backing off for {sleep_sec:.2f}s...")
                time.sleep(sleep_sec)
            else:
                logger.warning(f"HTTP {response.status_code} at {url} (Attempt {attempt}/{max_retries})")
                time.sleep(1.0)
        except requests.RequestException as e:
            logger.warning(f"Network error on {url} (Attempt {attempt}/{max_retries}): {e}")
            time.sleep(backoff_base ** attempt)
    return None


def extract_listings_from_html(html: str, region_meta: Dict[str, str]) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__srp_seo_rescue")
    if not tag or not tag.string:
        return []
    
    try:
        data = json.loads(tag.string)
    except json.JSONDecodeError:
        return []

    listings = data.get("listings", [])
    structured_items = data.get("structuredData", {}).get("itemList", {}).get("items", [])
    
    # Map structured items by URL or index
    struct_map = {}
    for it in structured_items:
        u = it.get("url")
        if u:
            struct_map[u] = it

    combined = []
    for idx, listing in enumerate(listings):
        u = listing.get("url")
        struct = struct_map.get(u) if u else None
        if not struct and idx < len(structured_items):
            struct = structured_items[idx]
        
        record = {
            "title": listing.get("title") or (struct.get("name") if struct else None),
            "url": "https://www.rumah123.com" + u if u and not u.startswith("http") else u,
            "raw_price": listing.get("price"),
            "display_location": listing.get("location"),
            "property_type": listing.get("propertyType", "Apartemen"),
            "short_description": listing.get("shortDescription"),
            "target_city": region_meta["city_name"],
            "target_province": region_meta["province"],
            "address_locality": struct.get("addressLocality") if struct else None,
            "address_region": struct.get("addressRegion") if struct else None,
            "bedrooms": struct.get("numberOfBedrooms") if struct else None,
            "bathrooms": struct.get("numberOfBathroomsTotal") if struct else None,
            "floor_size_m2": struct.get("floorSize") if struct else None,
            "latitude": struct.get("latitude") if struct else None,
            "longitude": struct.get("longitude") if struct else None,
            "image_url": listing.get("image") or (struct.get("image") if struct else None)
        }
        combined.append(record)
    return combined


def run_ingestion_pipeline(pages_per_region: int = 5, output_dir: str = "data/raw") -> str:
    os.makedirs(output_dir, exist_ok=True)
    all_extracted_records = []
    total_regions = len(TARGET_REGIONS)
    
    logger.info(f"Starting ingestion: {total_regions} regions, up to {pages_per_region} pages/region...")

    for r_idx, region in enumerate(TARGET_REGIONS, start=1):
        slug = region["region_slug"]
        city = region["city_name"]
        region_count = 0
        
        logger.info(f"[{r_idx}/{total_regions}] Fetching listings for {city} ({slug})...")
        
        for p in range(1, pages_per_region + 1):
            url = f"https://www.rumah123.com/sewa/{slug}/apartemen/?page={p}"
            html = fetch_page_with_retry(url)
            if not html:
                logger.warning(f"Failed to fetch page {p} for {city}. Skipping remaining pages.")
                break
            
            page_records = extract_listings_from_html(html, region)
            if not page_records:
                logger.info(f"No records found on page {p} for {city}. End of results.")
                break
            
            all_extracted_records.extend(page_records)
            region_count += len(page_records)
            
            # Politeness delay
            time.sleep(random.uniform(0.6, 1.2))

        logger.info(f"Completed {city}: Ingested {region_count} listings.")

    raw_output_path = os.path.join(output_dir, "raw_rental_listings_staged.json")
    with open(raw_output_path, "w", encoding="utf-8") as f:
        json.dump(all_extracted_records, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Ingestion finished! Saved {len(all_extracted_records)} raw listings to {raw_output_path}")
    return raw_output_path


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_out = os.path.join(base_dir, "data", "raw")
    # Quick CLI test run (3 pages per region)
    pages = 3 if "--test" in sys.argv else 5
    run_ingestion_pipeline(pages_per_region=pages, output_dir=target_out)
