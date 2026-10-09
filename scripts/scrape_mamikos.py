import requests, json, base64, time, urllib.parse
from Crypto.Cipher import AES
from typing import List, Dict, Any

KEY = bytes.fromhex('3339633835326430643062633432656638336637643364373038663432333638')
IV = bytes.fromhex('35646635613130656262303335303937')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'

def decrypt_rooms(j: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = base64.b64decode(j['rooms'])
    pt = AES.new(KEY, AES.MODE_CBC, IV).decrypt(raw)
    return json.loads(pt[:-pt[-1]].decode())

def scrape_city(session: requests.Session, city: str, max_pages: int = None) -> List[Dict[str, Any]]:
    """Scrape all pages for a city. Returns list of raw room dicts."""
    all_rooms = []
    offset = 0
    page = 0
    while True:
        body = {
            'filters': {
                'furnished': 'all',
                'price_range': [0, 50000000],
                'property_type': 'apartment',
                'rent_type': 2,  # bulanan
                'room_name': '',
                'random_seeds': 91,
                'area': city
            },
            'sorting': {'field': 'price', 'direction': '-'},
            'referrer': 'promo',
            'include_promoted': True,
            'include_premium': True,
            'limit': 20,
            'offset': offset,
            'location': []
        }
        r = session.post('https://mamikos.com/garuda/apartment', json=body, timeout=30)
        if not r.headers.get('content-type', '').startswith('application/json'):
            print(f'  [{city}] HTTP {r.status_code} non-json, stop')
            break
        j = r.json()
        if not j.get('status'):
            print(f'  [{city}] API status false: {j.get("meta")}')
            break
        rooms = decrypt_rooms(j)
        if not rooms:
            print(f'  [{city}] empty page, stop')
            break
        all_rooms.extend(rooms)
        page += 1
        print(f'  [{city}] page {page} offset {offset} got {len(rooms)} total {j.get("total")} has-more {j.get("has-more")}')
        if not j.get('has-more'):
            break
        offset = j.get('next-offset', offset + 20)
        if max_pages and page >= max_pages:
            break
        time.sleep(2.0)  # polite
    return all_rooms

def main():
    S = requests.Session()
    S.headers.update({
        'User-Agent': UA,
        'Accept-Language': 'id-ID,id;q=0.9',
        'Origin': 'https://mamikos.com',
        'Referer': 'https://mamikos.com/apartemen/sewa/jakarta-selatan/bulanan/all/',
        'Content-Type': 'application/json',
    })
    # init session cookie
    S.get('https://mamikos.com/apartemen/sewa/jakarta-selatan/bulanan/all/', timeout=30)
    xsrf = urllib.parse.unquote(S.cookies.get('XSRF-TOKEN') or '')
    S.headers['X-XSRF-TOKEN'] = xsrf

    jabodetabek = [
        "Jakarta Selatan", "Jakarta Pusat", "Jakarta Barat", "Jakarta Timur", "Jakarta Utara",
        "Tangerang", "Tangerang Selatan", "Depok", "Bekasi", "Bogor"
    ]

    all_data = []
    for city in jabodetabek:
        print(f'=== {city} ===')
        rooms = scrape_city(S, city)
        for rm in rooms:
            rm['_source_city_query'] = city
        all_data.extend(rooms)
        time.sleep(3.0)

    # write raw
    import os
    out_dir = 'data/raw'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'scrap_v3_mamikos_raw.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f'Done: {len(all_data)} records -> {out_path}')

if __name__ == '__main__':
    main()