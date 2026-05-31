"""Seed database — import real items from DeltaForcePrice + known combat readiness values."""
import requests
import database as db

PRICE_URL = "https://raw.githubusercontent.com/orzice/DeltaForcePrice/master/price.json"

# Known combat readiness values for popular 卡战备 items
# Format: game_item_name -> combat_readiness
KNOWN_CR = {
    # 武器
    "G18": 55000,
    "Uzi": 65000,
    "MP5": 72000,
    "M249": 85000,
    "勇士": 60000,
    # 头盔
    "户外棒球帽": 12000,
    "DICH 训练头盔": 30000,
    "DICH 训练头盔 (破损全面)": 28000,
    "MC201 防弹头盔": 45000,
    "MC201 防弹头盔 (破损全面)": 40000,
    "GT1 战术头盔": 65000,
    "DAS 防弹头盔": 80000,
    # 护甲/胸挂
    "轻型防弹衣": 25000,
    "标准防弹衣": 40000,
    "重型防弹衣": 60000,
    "突击者战术背心": 85000,
    # 背包
    "轻型背包": 8000,
    "GA 野战背包": 20000,
    "GT1 户外登山包": 38000,
    "MAP 侦查背包": 44000,
    "大型军用背包": 60000,
    # 胸挂
    "轻型胸挂": 6000,
    "G01 战术弹挂": 12000,
    "DSA 战术胸挂": 18000,
    "HD3 战术胸挂": 25000,
}

# Map price.json categories to our gear slots
CATEGORY_SLOT_MAP = {
    # Weapons → slot "武器"
    "手枪": "武器", "冲锋枪": "武器", "突击步枪": "武器",
    "精确射手步枪": "武器", "霰弹枪": "武器", "狙击步枪": "武器",
    "轻机枪": "武器", "战斗步枪": "武器",
    # Gear → individual slots
    "头盔": "头盔",
    "护甲": "护甲",
    "胸挂": "胸挂",
    "背包": "背包",
    # Attachments → slot "配件" (can equip multiple)
    "瞄具": "配件", "枪口": "配件", "握把": "配件",
    "弹匣": "配件", "枪管": "配件", "枪托": "配件",
    "前握把": "配件", "后握把": "配件", "枪木": "配件",
    "拉机柄": "配件", "机匣": "配件",
}

def import_from_price_json():
    """Import items from price.json, categorizing by gear slot."""
    try:
        resp = requests.get(PRICE_URL, timeout=30, headers={"User-Agent": "DeltaGear/1.0"})
        resp.encoding = "utf-8"
        data = resp.json()
    except Exception as e:
        print(f"Failed to fetch price.json: {e}")
        return 0

    imported = 0
    for item in data:
        name = item.get("name", "")
        cat = item.get("secondClassCN", "")
        slot = CATEGORY_SLOT_MAP.get(cat)
        if not slot:
            continue  # Skip ammo, collectibles, keys, etc.

        # 战备值: use known value if available, otherwise estimate from category
        cr = 0
        for key, val in KNOWN_CR.items():
            if key in name:
                cr = val
                break

        # If no known CR, estimate
        if cr == 0 and item.get("price", 0) > 0:
            # Most gear has 战备值 near market price; 破损 items may differ
            if "破损" in name:
                cr = int(item["price"] * 0.85)  # broken items: CR slightly below market
            else:
                cr = int(item["price"] * 1.05)  # normal: CR close to market

        db.add_item(name, cat, slot, cr, "auto-imported")

        # Save initial price
        price = item.get("price", 0)
        if price > 0:
            # Need to get item_id after insert
            items = {it["name"]: it["id"] for it in db.get_all_items()}
            if name in items:
                db.save_price(items[name], price)

        imported += 1

    return imported


def seed():
    db.init_db()

    # Maps
    maps = [
        ("零号大坝", "机密", 112500),
        ("长弓溪谷", "机密", 112500),
        ("巴克什", "机密", 187500),
        ("航天基地", "机密", 187500),
        ("巴克什", "绝密", 550000),
        ("航天基地", "绝密", 600000),
    ]
    for name, diff, threshold in maps:
        db.add_map(name, diff, threshold)
    print(f"Maps: {len(maps)}")

    # Import items from price.json
    n = import_from_price_json()
    print(f"Items imported: {n}")


if __name__ == "__main__":
    seed()
