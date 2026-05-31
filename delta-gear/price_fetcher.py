"""Price data fetcher — FREE real-time prices from DeltaForcePrice community project."""
import requests
import database as db
from datetime import datetime, timezone

# DeltaForcePrice — free, open source, updated every 10 min
# GitHub: https://github.com/orzice/DeltaForcePrice
PRICE_JSON_URL = "https://raw.githubusercontent.com/orzice/DeltaForcePrice/master/price.json"

def fetch_price_json():
    """Fetch latest prices from DeltaForcePrice (free, real-time)."""
    try:
        resp = requests.get(
            PRICE_JSON_URL,
            timeout=30,
            headers={"User-Agent": "DeltaGear/1.0"},
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Price fetch failed: {e}")
        return None

def save_prices(data: list[dict]):
    """Match price.json items to our DB by name and save prices."""
    items = list(db.get_all_items())
    name_to_id = {it["name"]: it["id"] for it in items}
    saved = 0

    for row in data:
        name = row.get("name", "")
        price = row.get("price", 0)
        if name in name_to_id and price > 0:
            db.save_price(name_to_id[name], price)
            saved += 1

    return saved

def refresh_prices(mode: str = "auto"):
    """
    Refresh all prices.
    - "live": real prices from DeltaForcePrice GitHub
    - "mock": simulated prices for demo
    - "auto": try live first, fallback to mock
    """
    if mode == "mock":
        return mock_refresh()

    data = fetch_price_json()
    if data:
        saved = save_prices(data)
        if saved > 0:
            update_time = data[0].get("is_get_time", 0) if data else 0
            return {"source": "交易行实时数据 (免费)", "saved": saved, "items_total": len(data)}

    if mode == "live":
        return {"source": "none", "saved": 0, "error": "无法获取实时数据，请检查网络连接"}

    return mock_refresh()

def mock_refresh():
    """Generate simulated prices (demo fallback)."""
    import random
    random.seed()

    items = list(db.get_all_items())
    saved = 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    for it in items:
        cr = it["combat_readiness"]
        if cr <= 0:
            continue
        if "破损" in it["name"] or "旧" in it["name"]:
            multiplier = random.uniform(0.15, 0.4)
        else:
            multiplier = random.uniform(0.7, 1.3)
        price = round(cr * multiplier, -2)
        db.save_price(it["id"], price)
        saved += 1

    return {"source": "模拟数据", "saved": saved, "time": now}
