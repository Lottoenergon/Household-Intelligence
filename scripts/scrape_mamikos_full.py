import requests, json, base64, urllib.parse, time, os
from Crypto.Cipher import AES

KEY = bytes.fromhex('3339633835326430643062633432656638336637643364373038663432333638')
IV = bytes.fromhex('35646635613130656262303335303937')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'

def decrypt_rooms(j):
    raw = base64.b64decode(j['rooms'])
    pt = AES.new(KEY, AES.MODE_CBC, IV).decrypt(raw)
    return json.loads(pt[:-pt[-1]].decode())

def make_session():
    S = requests.Session()
    S.headers.update({
        'User-Agent': UA,
        'Accept-Language': 'id-ID,id;q=0.9',
        'Origin': 'https://mamikos.com',
        'Referer': 'https://mamikos.com/apartemen/sewa/jakarta-selatan/bulanan/all/',
        'Content-Type': 'application/json',
        'X-GIT-Time': '1406090202',
        'Authorization': 'GIT WEB:WEB',
    })
    S.get('https://mamikos.com/apartemen/sewa/jakarta-selatan/bulanan/all/', timeout=30)
    S.headers['X-XSRF-TOKEN'] = urllib.parse.unquote(S.cookies.get('XSRF-TOKEN') or '')
    return S

def scrape_city(S, city, max_offset=None):
    """Scrape all pages for a city using per-city filter."""
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
        r = S.post('https://mamikos.com/garuda/apartment', json=body, timeout=30)
        if not r.headers.get('content-type', '').startswith('application/json'):
            print(f'  [{city}] HTTP {r.status_code} non-json, stop')
            break
        j = r.json()
        if not j.get('status'):
            print(f'  [{city}] API status false')
            break
        rooms = decrypt_rooms(j)
        if not rooms:
            print(f'  [{city}] empty page at offset {offset}, stop')
            break
        all_rooms.extend(rooms)
        page += 1
        total = j.get('total', 0)
        has_more = j.get('has-more', False)
        next_offset = j.get('next-offset', offset + 20)
        print(f'  [{city}] p{page} off={offset} got={len(rooms)} total={total} more={has_more}')
        if not has_more:
            break
        offset = next_offset
        if max_offset and offset > max_offset:
            break
        time.sleep(2.0)
    return all_rooms

def scrape_national_dedup(S, max_pages=600):
    """Sweep national 'all' with dedup by _id, stop after N consecutive dup pages."""
    all_rooms = []
    seen = set()
    dup_pages = 0
    offset = 0
    for page in range(1, max_pages + 1):
        body = {
            'filters': {
                'furnished': 'all',
                'price_range': [0, 50000000],
                'property_type': 'apartment',
                'rent_type': 2,
                'room_name': '',
                'random_seeds': 91,
                'area': 'all'
            },
            'sorting': {'field': 'price', 'direction': '-'},
            'referrer': 'promo',
            'include_promoted': True,
            'include_premium': True,
            'limit': 20,
            'offset': offset,
            'location': []
        }
        r = S.post('https://mamikos.com/garuda/apartment', json=body, timeout=30)
        if not r.headers.get('content-type', '').startswith('application/json'):
            print(f'  [NATIONAL] HTTP {r.status_code} non-json')
            break
        j = r.json()
        if not j.get('status'):
            break
        rooms = decrypt_rooms(j)
        if not rooms:
            break
        new_ids = [r['_id'] for r in rooms if r['_id'] not in seen]
        seen.update(r['_id'] for r in rooms)
        if new_ids:
            all_rooms.extend([r for r in rooms if r['_id'] in new_ids])
            dup_pages = 0
        else:
            dup_pages += 1
        total = j.get('total', 0)
        has_more = j.get('has-more', False)
        next_offset = j.get('next-offset', offset + 20)
        if page % 20 == 0:
            print(f'  [NATIONAL] p{page} off={offset} got={len(rooms)} new={len(new_ids)} uniq={len(seen)} more={has_more}')
        if dup_pages >= 5:
            print(f'  [NATIONAL] STOP: {dup_pages} consecutive dup pages at offset {offset}')
            break
        offset = next_offset
        if not has_more:
            break
        time.sleep(1.5)
    return all_rooms

def main():
    S = make_session()

    # 1. Cities with working per-city filter
    working_cities = [
        "Jakarta Selatan", "Jakarta Pusat", "Jakarta Barat", "Jakarta Timur", "Jakarta Utara",
        "Tangerang", "Depok", "Bekasi"
    ]

    all_data = []
    for city in working_cities:
        print(f'=== {city} ===')
        rooms = scrape_city(S, city)
        for rm in rooms:
            rm['_source_city_query'] = city
        all_data.extend(rooms)
        time.sleep(3.0)

    # 2. National sweep for Tangsel & Bogor (filter broken)
    print('=== NATIONAL sweep (Tangsel+Bogor gap) ===')
    nat_rooms = scrape_national_dedup(S, max_pages=600)
    for rm in nat_rooms:
        rm['_source_city_query'] = 'all_national'
    all_data.extend(nat_rooms)

    S.close()

    # Write raw
    os.makedirs('data/raw', exist_ok=True)
    out_path = 'data/raw/scrap_v3_mamikos_raw.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f'\nDONE: {len(all_data)} records -> {out_path}')

if __name__ == '__main__':
    main()