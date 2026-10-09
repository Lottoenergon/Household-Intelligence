import json, re
from typing import List, Dict, Any, Optional

MAMIKOS_CITY_MAP = {
    "Jakarta Selatan": ("Jakarta Selatan", "DKI Jakarta"),
    "Kota Jakarta Selatan": ("Jakarta Selatan", "DKI Jakarta"),
    "Jakarta Pusat": ("Jakarta Pusat", "DKI Jakarta"),
    "Kota Jakarta Pusat": ("Jakarta Pusat", "DKI Jakarta"),
    "Jakarta Barat": ("Jakarta Barat", "DKI Jakarta"),
    "Jakarta Timur": ("Jakarta Timur", "DKI Jakarta"),
    "Kota Jakarta Timur": ("Jakarta Timur", "DKI Jakarta"),
    "Jakarta Utara": ("Jakarta Utara", "DKI Jakarta"),
    "Kota Jakarta Utara": ("Jakarta Utara", "DKI Jakarta"),
    "North Jakarta": ("Jakarta Utara", "DKI Jakarta"),
    "Tangerang": ("Tangerang", "Banten"),
    "Kota Tangerang": ("Tangerang", "Banten"),
    "Tangerang Selatan": ("Tangerang Selatan", "Banten"),
    "Kota Tangerang Selatan": ("Tangerang Selatan", "Banten"),
    "Depok": ("Depok", "Jawa Barat"),
    "Kota Depok": ("Depok", "Jawa Barat"),
    "Bekasi": ("Bekasi", "Jawa Barat"),
    "Kota Bekasi": ("Bekasi", "Jawa Barat"),
    "Bogor": ("Bogor", "Jawa Barat"),
    "Kota Bogor": ("Bogor", "Jawa Barat"),
}

def parse_price(price_title_time: str) -> Optional[float]:
    """Convert '8.000.000 / bulan' to monthly IDR."""
    if not price_title_time:
        return None
    m = re.search(r'([\d\.]+)', price_title_time.replace('.', ''))
    if not m:
        return None
    val = float(m.group(1))
    if '/ hari' in price_title_time.lower():
        return val * 30
    if '/ minggu' in price_title_time.lower():
        return val * 4.33
    if '/ tahun' in price_title_time.lower():
        return val / 12
    return val

def parse_bedrooms(unit_type: str, unit_type_rooms: dict) -> int:
    if unit_type_rooms and 'bedroom' in unit_type_rooms:
        return int(unit_type_rooms['bedroom'])
    m = re.search(r'(\d+)\s*(?:BR|Kamar)', unit_type or '', re.I)
    if m:
        return int(m.group(1))
    if unit_type and 'Studio' in unit_type:
        return 1
    return 1

def parse_bathrooms(unit_type_rooms: dict) -> int:
    if unit_type_rooms and 'bathroom' in unit_type_rooms:
        return int(unit_type_rooms['bathroom'])
    return 1

def parse_floor_size(size: Any) -> float:
    try:
        return float(size) if size else None
    except:
        return None

def extract_subdistrict(area_label: str) -> str:
    """Extract subdistrict from 'Mampang Prapatan, Jakarta Selatan, Jakarta'."""
    if not area_label:
        return None
    parts = [p.strip() for p in area_label.split(',') if p.strip()]
    return parts[0] if parts else None

def map_mamikos(raw_records: List[Dict]) -> List[Dict[str, Any]]:
    seen = {}
    for r in raw_records:
        uid = r.get('_id')
        if uid and uid not in seen:
            seen[uid] = r
    unique = list(seen.values())
    
    out = []
    for r in unique:
        city_raw = r.get('city') or r.get('subdistrict', '')
        target_city, target_province = MAMIKOS_CITY_MAP.get(city_raw, (None, None))
        if not target_city:
            continue
            
        rec = {
            "title": r.get('room-title', '').strip(),
            "url": r.get('share_url', '').strip(),
            "raw_price": r.get('price_title_time', '').strip(),
            "display_location": f"{extract_subdistrict(r.get('area_label',''))}, {target_city}",
            "property_type": "Apartemen",
            "short_description": f"{r.get('room-title','')} | {r.get('area_label','')} | {r.get('unit_type','')} | {r.get('furnished_status','')}",
            "target_city": target_city,
            "target_province": target_province,
            "address_locality": extract_subdistrict(r.get('area_label','')),
            "address_region": target_city,
            "bedrooms": parse_bedrooms(r.get('unit_type'), r.get('unit_type_rooms')),
            "bathrooms": parse_bathrooms(r.get('unit_type_rooms')),
            "floor_size_m2": parse_floor_size(r.get('size')),
            "latitude": None,
            "longitude": None,
            "image_url": r.get('photo_url', {}).get('large', '') if isinstance(r.get('photo_url'), dict) else '',
            "source": "mamikos"
        }
        out.append(rec)
    return out

if __name__ == "__main__":
    import sys
    in_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/scrap_v3_mamikos_raw.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "data/raw/raw_mamikos_staged.json"
    
    with open(in_path, encoding="utf-8") as f:
        raw = json.load(f)
    mapped = map_mamikos(raw)
    
    import os
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(mapped, f, indent=2, ensure_ascii=False)
    print(f"Mapped {len(mapped)} unique mamikos records -> {out_path}")