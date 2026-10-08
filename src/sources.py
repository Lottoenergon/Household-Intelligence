"""
sources.py
Source adapter registry for Jabodetabek rental listings.

Every adapter returns records in the SAME raw schema that
transformation.py consumes (raw_rental_listings_staged.json), so downstream
code stays source-agnostic. Each adapter owns: URL building, fetch, parse,
and its own politeness delay (from robots.txt Crawl-delay).

Status:
- rumah123: adapter scrape_rumah123() wraps ingestion.extract_listings_from_html; delay 5s (robots Crawl-Delay).
- 99co:     SKELETON. Parser built from live __NEXT_DATA__ schema (verified),
            not yet wired into run_pipeline.py. Tests use fixture only.
"""

import json
import os
import re
import time
import random
import logging
from typing import Dict, Any, List, Optional, Callable

import requests

logger = logging.getLogger(__name__)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "id-ID,id;q=0.9,en;q=0.7"}

NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)

# Jakarta/Bekasi/Depok/... slugs as used by 99.co (same region list as ingestion.py)
TARGET_SLUGS_99CO = {
    "Jakarta Selatan": "jakarta-selatan",
    "Jakarta Pusat": "jakarta-pusat",
    "Jakarta Barat": "jakarta-barat",
    "Jakarta Timur": "jakarta-timur",
    "Jakarta Utara": "jakarta-utara",
    "Tangerang": "tangerang",
    "Tangerang Selatan": "tangerang-selatan",
    "Depok": "depok",
    "Bekasi": "bekasi",
    "Bogor": "bogor",
}

# Crawl-delay from https://www.99.co/robots.txt: rogerbot/dotbot = 3, * = none.
# rumah123 robots.txt: Crawl-Delay: 5 for *.
CRAWL_DELAY_SEC = {"rumah123": 5.0, "99co": 5.0}


def polite_sleep(source: str) -> None:
    base = CRAWL_DELAY_SEC[source]
    time.sleep(base + random.uniform(0.0, 1.0))


def fetch_text(url: str, timeout: int = 30) -> Optional[str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
        logger.warning("HTTP %s at %s", r.status_code, url)
    except requests.RequestException as e:
        logger.warning("Network error at %s: %s", url, e)
    return None


def _parse_next_data(html: str) -> Optional[Dict[str, Any]]:
    m = NEXT_DATA_RE.search(html)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------- 99.co ----

_99CO_PARAM = "hlmn"  # 99.co pagination param (verified live: ?hlmn=2 returns distinct listings; ?page= ignored)

def build_99co_url(city_slug: str, page: int) -> str:
    return f"https://www.99.co/id/sewa/apartemen/{city_slug}?{_99CO_PARAM}={page}"


def parse_99co_listings(html: str, region_meta: Dict[str, str]) -> List[Dict[str, Any]]:
    """Map 99.co __NEXT_DATA__ -> raw staged schema.

    Schema (verified live):
      props.pageProps.data.listings[*].data[*] = listing dict
        price.price_tag / price.price (IDR, per period in rent_type)
        rent_type.value in {daily, weekly, monthly, yearly}
        attributes.bedrooms / bathrooms / builtup_area.value (m2)
        attributes.interior.value  (furnish text)
        location.district.name / location.city.name
        location_pin.lat / .long   (CAUTION: sample had lat == long, corrupted)
    """
    d = _parse_next_data(html)
    if not d:
        return []
    try:
        groups = d["props"]["pageProps"]["data"]["listings"]
    except (KeyError, TypeError):
        return []

    out: List[Dict[str, Any]] = []
    for g in groups:
        for it in g.get("data", []) or []:
            attrs = it.get("attributes", {}) or {}
            price = it.get("price", {}) or {}
            loc = it.get("location", {}) or {}
            pin = it.get("location_pin", {}) or {}
            rent_type = (it.get("rent_type") or {}).get("value")

            # Normalize to the rumah123-style raw_price string that
            # transformation.parse_normalized_price understands.
            period_map = {"yearly": "/tahun", "monthly": "/bulan",
                          "weekly": "/minggu", "daily": "/hari"}
            raw_price = None
            if price.get("price_tag"):
                raw_price = f"{price['price_tag']} {period_map.get(rent_type, '/bulan')}".strip()

            builtup = (attrs.get("builtup_area") or {}).get("value")
            try:
                floor_m2 = float(builtup) if builtup not in (None, "") else None
            except ValueError:
                floor_m2 = None

            district = (loc.get("district") or {}).get("name") or ""
            city = (loc.get("city") or {}).get("name") or region_meta["city_name"]
            display_location = f"{district}, {city}" if district else city

            slug_url = it.get("url") or it.get("slug")
            url = (slug_url if slug_url and slug_url.startswith("http")
                   else f"https://www.99.co/id/properti/{slug_url}" if slug_url
                   else None)

            out.append({
                "title": it.get("title"),
                "url": url,
                "raw_price": raw_price,
                "display_location": display_location,
                "property_type": "Apartemen",
                "short_description": (it.get("description") or "")[:500],
                "target_city": region_meta["city_name"],
                "target_province": region_meta["province"],
                "address_locality": district or None,
                "address_region": (loc.get("province") or {}).get("name"),
                "bedrooms": attrs.get("bedrooms"),
                "bathrooms": attrs.get("bathrooms"),
                "floor_size_m2": floor_m2,
                "latitude": pin.get("lat"),
                "longitude": pin.get("long"),
                "image_url": None,
                "source": "99co",
            })
    return out


def scrape_99co(region_meta: Dict[str, str], pages: int = 3) -> List[Dict[str, Any]]:
    """Pagination ?hlmn= (verified live). Early-stop jk 2 halaman beruntun tanpa URL baru."""
    slug = TARGET_SLUGS_99CO[region_meta["city_name"]]
    records: List[Dict[str, Any]] = []
    seen: set = set()
    stale = 0
    for p in range(1, pages + 1):
        html = fetch_text(build_99co_url(slug, p))
        if not html:
            break
        page_recs = parse_99co_listings(html, region_meta)
        fresh = [r for r in page_recs if r.get("url") and r["url"] not in seen]
        for r in fresh:
            seen.add(r["url"])
        records.extend(fresh)
        stale = stale + 1 if not fresh else 0
        if stale >= 2:
            break
        polite_sleep("99co")
    return records


# ------------------------------------------------------------- rumah123 ----

def build_rumah123_url(region_slug: str, page: int) -> str:
    return f"https://www.rumah123.com/sewa/{region_slug}/apartemen/?page={page}"


def scrape_rumah123(region_meta: Dict[str, str], pages: int = 3) -> List[Dict[str, Any]]:
    """Wrap ingestion.extract_listings_from_html (parser existing, schema identik).

    Delay dari CRAWL_DELAY_SEC['rumah123'] (robots.txt Crawl-Delay: 5).
    Lazy import: ingestion.py punya basicConfig + bs4 dependency.
    """
    from ingestion import extract_listings_from_html, fetch_page_with_retry

    records: List[Dict[str, Any]] = []
    for p in range(1, pages + 1):
        html = fetch_page_with_retry(build_rumah123_url(region_meta["region_slug"], p))
        if not html:
            break
        page_recs = extract_listings_from_html(html, region_meta)
        if not page_recs:
            break
        records.extend(page_recs)
        polite_sleep("rumah123")
    return records


# ------------------------------------------------------------- registry ----

ADAPTERS: Dict[str, Callable[..., List[Dict[str, Any]]]] = {
    "99co": scrape_99co,
    "rumah123": scrape_rumah123,
}


def run_source(name: str, out_dir: str, pages: int = 3,
               regions: Optional[List[Dict[str, str]]] = None) -> str:
    """Scrape satu source untuk semua region, tulis ke raw_<name>_staged.json.

    Output TERPISAH dari raw_rental_listings_staged.json (produksi). Merge dilakukan
    terpisah setelah dedup URL.
    """
    import os
    if name not in ADAPTERS:
        raise ValueError(f"Unknown source {name!r}. Available: {sorted(ADAPTERS)}")
    if regions is None:
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from ingestion import TARGET_REGIONS
        regions = TARGET_REGIONS
    os.makedirs(out_dir, exist_ok=True)
    records: List[Dict[str, Any]] = []
    for region in regions:
        recs = ADAPTERS[name](region, pages=pages)
        logger.info("%s %s: %d listings", name, region["city_name"], len(recs))
        records.extend(recs)
    out_path = os.path.join(out_dir, f"raw_{name}_staged.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    logger.info("%s: %d listings -> %s", name, len(records), out_path)
    return out_path


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, choices=sorted(ADAPTERS))
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--out-dir", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw"))
    a = ap.parse_args()
    run_source(a.source, a.out_dir, pages=a.pages)

