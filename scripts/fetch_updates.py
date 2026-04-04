import json
import re
import urllib.request
import urllib.parse
import os
from datetime import date

API_URL = "https://www.microsoft.com/releasecommunications/api/v2/azure"
FILTER = "created ge 2026-03-09T00:00:00Z and created le 2026-04-03T23:59:59Z"
TOP = 200
ORDER_BY = "created desc"

def strip_html(html_text):
    if not html_text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', html_text)
    text = re.sub(r'</li>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('\u00a0', ' ')
    text = text.replace('\u200b', '')
    text = text.replace('\u202f', ' ')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

def fetch_all():
    all_items = []
    skip = 0
    while True:
        params = urllib.parse.urlencode({
            "$top": TOP,
            "$skip": skip,
            "$orderby": ORDER_BY,
            "$filter": FILTER,
        })
        url = f"{API_URL}?{params}"
        print(f"Fetching: {url}")
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        items = data.get('value', [])
        if not items:
            break
        all_items.extend(items)
        if len(items) < TOP:
            break
        skip += TOP
    return all_items

def transform(item):
    return {
        "id": item.get("id"),
        "title": (item.get("title") or "").strip(),
        "description": strip_html(item.get("description", "")),
        "status": item.get("status"),
        "created": item.get("created"),
        "modified": item.get("modified"),
        "productCategories": item.get("productCategories", []),
        "tags": item.get("tags", []),
        "products": item.get("products", []),
        "generalAvailabilityDate": item.get("generalAvailabilityDate"),
        "previewAvailabilityDate": item.get("previewAvailabilityDate"),
        "availabilities": item.get("availabilities", []),
    }

def main():
    today = date.today().strftime("%Y%m%d")
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", today)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "updates.json")

    raw_items = fetch_all()
    print(f"Fetched {len(raw_items)} items from API")

    results = [transform(item) for item in raw_items]

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} items to {out_path}")

if __name__ == "__main__":
    main()
