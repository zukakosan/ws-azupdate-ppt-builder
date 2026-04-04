import json
import re
import urllib.request
import urllib.parse
from html import unescape
from datetime import datetime

BASE_URL = "https://www.microsoft.com/releasecommunications/api/v2/azure"
START_DATE = "2026-03-06T00:00:00Z"
END_DATE = "2026-04-04T00:00:00Z"  # inclusive of April 3rd full day

def strip_html(html_text):
    """Remove HTML tags and decode entities."""
    if not html_text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', html_text)
    text = re.sub(r'</li>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def fetch_all_updates():
    all_items = []
    top = 100
    skip = 0

    odata_filter = f"created ge '{START_DATE}' and created le '{END_DATE}'"

    while True:
        params = {
            "$top": str(top),
            "$skip": str(skip),
            "$orderby": "created desc",
            "$filter": odata_filter
        }
        url = BASE_URL + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        print(f"Fetching: skip={skip} ...")

        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"HTTP Error {e.code}: {e.reason}")
            # Try without filter and do client-side filtering
            print("Trying without server-side filter...")
            return fetch_all_updates_no_filter()

        items = data.get("value", [])
        if not items:
            break

        all_items.extend(items)
        print(f"  Got {len(items)} items (total so far: {len(all_items)})")

        if len(items) < top:
            break
        skip += top

    return all_items

def fetch_all_updates_no_filter():
    """Fallback: fetch large batches and filter client-side."""
    all_items = []
    top = 100
    skip = 0
    start_dt = datetime.fromisoformat(START_DATE.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(END_DATE.replace("Z", "+00:00"))

    while True:
        params = {
            "$top": str(top),
            "$skip": str(skip),
            "$orderby": "created desc",
        }
        url = BASE_URL + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        print(f"Fetching (no filter): skip={skip} ...")

        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")

        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = data.get("value", [])
        if not items:
            break

        found_before_start = False
        for item in items:
            created_str = item.get("created", "")
            try:
                created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except ValueError:
                continue

            if created_dt < start_dt:
                found_before_start = True
                continue
            if created_dt <= end_dt:
                all_items.append(item)

        print(f"  Got {len(items)} items, matched so far: {len(all_items)}")

        if found_before_start or len(items) < top:
            break
        skip += top

    return all_items

def transform_item(item):
    return {
        "id": item.get("id"),
        "title": (item.get("title") or "").strip(),
        "description": strip_html(item.get("description", "")),
        "status": item.get("status") or None,
        "created": item.get("created"),
        "modified": item.get("modified"),
        "productCategories": item.get("productCategories", []),
        "tags": item.get("tags", []),
        "products": item.get("products", []),
        "generalAvailabilityDate": item.get("generalAvailabilityDate"),
        "previewAvailabilityDate": item.get("previewAvailabilityDate"),
        "availabilities": item.get("availabilities", []),
        "link": f"https://azure.microsoft.com/updates/?id={item.get('id')}"
    }

if __name__ == "__main__":
    print("Fetching Azure Updates...")
    raw_items = fetch_all_updates()
    print(f"\nTotal raw items in date range: {len(raw_items)}")

    results = [transform_item(item) for item in raw_items]

    output_path = "output/updates.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} items to {output_path}")
