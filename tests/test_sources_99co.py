"""99.co adapter: parse fixture -> raw staged schema consumed by transformation.py."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import sources as S
from transformation import parse_normalized_price

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "99co_sewa_apartemen_sample.html")
REGION = {"city_name": "Jakarta Selatan", "province": "DKI Jakarta"}

# Must match the keys ingestion.extract_listings_from_html emits for rumah123.
RAW_KEYS = {
    "title", "url", "raw_price", "display_location", "property_type",
    "short_description", "target_city", "target_province", "address_locality",
    "address_region", "bedrooms", "bathrooms", "floor_size_m2",
    "latitude", "longitude", "image_url",
}


def _recs():
    with open(FIXTURE, encoding="utf-8") as f:
        return S.parse_99co_listings(f.read(), REGION)


def test_schema_superset_of_rumah123_raw():
    recs = _recs()
    assert len(recs) == 4
    for r in recs:
        assert RAW_KEYS <= set(r), RAW_KEYS - set(r)
        assert r["source"] == "99co"
        assert r["url"].startswith("https://www.99.co/id/properti/")


def test_price_normalizes_to_monthly():
    for r in _recs():
        monthly, period, outlier = parse_normalized_price(r["raw_price"])
        assert monthly and monthly > 0
        assert period in {"monthly", "yearly"}
        assert not outlier


def test_yearly_price_divided_by_12():
    r = _recs()[0]  # Rp 180 Juta /tahun
    assert parse_normalized_price(r["raw_price"])[0] == 15_000_000


def test_empty_or_bad_html_returns_empty():
    assert S.parse_99co_listings("<html></html>", REGION) == []
    assert S.parse_99co_listings('<script id="__NEXT_DATA__">{bad</script>', REGION) == []


def test_crawl_delay_not_below_robots():
    assert S.CRAWL_DELAY_SEC["rumah123"] >= 5.0
    assert S.CRAWL_DELAY_SEC["99co"] >= 3.0


def test_rumah123_url_matches_ingestion():
    # Template URL adapter harus identik dengan ingestion.py loop utama.
    assert S.build_rumah123_url("jakarta-selatan", 1) == \
        "https://www.rumah123.com/sewa/jakarta-selatan/apartemen/?page=1"


def test_rumah123_adapter_registered_and_delayed():
    assert "rumah123" in S.ADAPTERS
    assert S.CRAWL_DELAY_SEC["rumah123"] >= 5.0


def test_99co_pagination_uses_hlmn_not_page():
    # Regression: 99.co uses ?hlmn= for pagination, not ?page=
    # Page 1 vs page 2 must return distinct listings (0 overlap)
    import requests, re, json
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    H = {"User-Agent": UA, "Accept-Language": "id-ID,id;q=0.9"}
    def ids(hlmn):
        h = requests.get(f"https://www.99.co/id/sewa/apartemen/jakarta-selatan?hlmn={hlmn}", headers=H, timeout=30).text
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', h, re.S)
        d = json.loads(m.group(1))
        L = d["props"]["pageProps"]["data"]["listings"]
        out = []
        for g in L:
            for it in g.get("data", []):
                out.append(it.get("id") or it.get("property_id"))
        return set(out)
    p1 = ids(1)
    p2 = ids(2)
    assert p1 and p2
    assert len(p1 & p2) == 0, f"pagination overlap: {p1 & p2}"
    # URL builder must use hlmn
    assert S.build_99co_url("jakarta-selatan", 1).endswith("?hlmn=1")
    assert S.build_99co_url("jakarta-selatan", 2).endswith("?hlmn=2")
    assert "?page=" not in S.build_99co_url("jakarta-selatan", 1)
