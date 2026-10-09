"""Geocode canonical apartment projects via Nominatim (OSM), cached & resumable.

Kenapa perlu: pin koordinat dari portal (99.co/Rumah123) sering salah tempat
(broker taruh pin di kantor agen, bukan di gedung). Median koordinat listing
per project jadi terkontaminasi -> model justru turun kalau dipakai mentah.
Nominatim memberi koordinat gedung resmi dari OSM.

Kota tiap project diambil dari kolom `target_city` listing yang resolve ke
project itu (registry city sering kosong/null -> query 'X, Jakarta' meleset
untuk project Depok/Bekasi/Bogor/Tangerang).

Output: data/project_coordinates.json  (resumable: skip project yang sudah ada)
Etika Nominatim: User-Agent jelas + >=1 detik antar request (rate limit resmi 1 rps).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(BASE_DIR, "data", "property_registry.json")
CLEANED = os.path.join(BASE_DIR, "data", "processed", "jabodetabek_rental_cleaned.csv")
OUT = os.path.join(BASE_DIR, "data", "project_coordinates.json")
CACHE_RAW = os.path.join(BASE_DIR, "data", "project_geocode_raw.json")
USER_AGENT = "HouseholdIntelligence/1.0 (portfolio project; contact: afiattailhan.ai@gmail.com)"
SLEEP_S = 1.1


def geocode(query: str):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": query, "format": "json", "limit": 1, "countrycodes": "id",
    })
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        return None, str(exc)
    if not data:
        return None, "not_found"
    top = data[0]
    return {
        "lat": float(top["lat"]), "lon": float(top["lon"]),
        "display_name": top.get("display_name", ""),
        "osm_type": top.get("osm_type"), "osm_id": top.get("osm_id"),
        "type": top.get("type"),
    }, None


def build_city_map():
    """project_id -> kota dominan dari listing yang resolve ke project tsb."""
    sys.path.insert(0, os.path.join(BASE_DIR, "src"))
    import pandas as pd
    from entity_resolution import resolve
    if not os.path.exists(CLEANED):
        return {}
    df = pd.read_csv(CLEANED)
    pids = [resolve(t, u).get("project_id") for t, u in zip(df["title"], df["url"])]
    df["project_id"] = pids
    sub = df.dropna(subset=["project_id"])
    return sub.groupby("project_id")["target_city"].agg(
        lambda s: s.mode().iloc[0] if len(s) else None).to_dict()


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def main():
    registry = load_json(REGISTRY, {"projects": []})
    coords = load_json(OUT, {})
    raw = load_json(CACHE_RAW, {})
    city_map = build_city_map()
    print(f"City map resolved for {len(city_map)} projects", flush=True)

    todo = [p for p in registry["projects"] if p["id"] not in coords]
    print(f"Projects: {len(registry['projects'])} | geocoded: {len(coords)} | todo: {len(todo)}", flush=True)

    for i, p in enumerate(todo, 1):
        pid, name = p["id"], p["name"]
        city = city_map.get(pid) or p.get("city") or "Jakarta"
        queries = [
            f"{name}, {city}, Indonesia",
            f"Apartment {name}, {city}, Indonesia",
            f"{name}, Indonesia",
        ]
        hit = None
        err = None
        for q in queries:
            res, err = geocode(q)
            time.sleep(SLEEP_S)
            if res:
                hit = (q, res)
                break
        if hit:
            q, res = hit
            coords[pid] = {"lat": res["lat"], "lon": res["lon"], "name": name,
                           "city": city, "display_name": res["display_name"],
                           "query": q, "source": "nominatim"}
            raw[pid] = {"query": q, "result": res, "project_name": name, "city": city}
            print(f"[{i}/{len(todo)}] OK   {name} ({city})", flush=True)
        else:
            raw[pid] = {"query": queries[0], "result": None, "error": err,
                        "project_name": name, "city": city}
            print(f"[{i}/{len(todo)}] MISS {name} ({city})", flush=True)
        if i % 10 == 0:
            save_json(OUT, coords)
            save_json(CACHE_RAW, raw)

    save_json(OUT, coords)
    save_json(CACHE_RAW, raw)
    print(f"DONE. Geocoded {len(coords)}/{len(registry['projects'])} projects -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
