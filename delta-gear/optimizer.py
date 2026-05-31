"""Gear optimizer — fast minimum-cost loadout calculation with attachments."""

BASE_SLOTS = ["武器", "头盔", "护甲", "背包", "胸挂"]
ATTACH_SLOT = "配件"
MAX_ATTACHMENTS = 5

def calculate(threshold: int, items_by_slot: dict, slot_required: dict = None):
    """
    Find minimum-cost gear combo meeting combat readiness threshold.
    Supports multi-pick attachments for maximum 战备 efficiency.
    """
    if slot_required is None:
        slot_required = {s: True for s in BASE_SLOTS}

    # Step 1: Pre-compute best attachment combos
    attachments = items_by_slot.get(ATTACH_SLOT, [])
    # Sort by efficiency
    attachments_sorted = sorted(
        attachments,
        key=lambda x: x["cr"] / max(x["price"], 1),
        reverse=True
    )
    # Top 30 most efficient attachments for combo generation
    top_atts = attachments_sorted[:30]

    # Generate best combos: pick 0, 1, 2, 3, 4, 5 attachments
    att_combos = [{"items": [], "price": 0, "cr": 0, "label": "无配件"}]
    for n in range(1, MAX_ATTACHMENTS + 1):
        best = sorted(top_atts, key=lambda x: x["cr"] / max(x["price"], 1), reverse=True)[:n]
        att_combos.append({
            "items": [{"name": a["name"], "price": a["price"], "cr": a["cr"]} for a in best],
            "price": sum(a["price"] for a in best),
            "cr": sum(a["cr"] for a in best),
            "label": f"{n}件配件",
        })

    # Step 2: Trim base slots to top 8
    trimmed = {}
    for slot in BASE_SLOTS:
        opts = items_by_slot.get(slot, [])
        if not slot_required.get(slot, True):
            opts = [{"name": "无", "price": 0, "cr": 0}] + opts
        opts.sort(key=lambda x: x["cr"] / max(x["price"], 1), reverse=True)
        trimmed[slot] = opts[:8] if opts else [{"name": "无", "price": 0, "cr": 0}]
        if not trimmed[slot]:
            trimmed[slot] = [{"name": "无", "price": 0, "cr": 0}]

    # Step 3: Enumerate base combinations × attachment combos
    from itertools import product
    slot_names = list(trimmed.keys())
    slot_options = [trimmed[s] for s in slot_names]

    best = None
    for base_items in product(*slot_options):
        base_cr = sum(it["cr"] for it in base_items)
        base_price = sum(it["price"] for it in base_items)

        # Try each attachment combo
        for att_combo in att_combos:
            total_cr = base_cr + att_combo["cr"]
            total_price = base_price + att_combo["price"]
            if total_cr >= threshold:
                if best is None or total_price < best["total_price"]:
                    gear = [
                        {"slot": slot_names[i], "name": base_items[i]["name"],
                         "price": base_items[i]["price"], "cr": base_items[i]["cr"]}
                        for i in range(len(base_items))
                        if base_items[i]["name"] != "无"
                    ]
                    for a in att_combo["items"]:
                        gear.append({"slot": ATTACH_SLOT, "name": a["name"],
                                     "price": a["price"], "cr": a["cr"]})
                    best = {"total_price": total_price, "total_cr": total_cr, "items": gear}

    if best is None:
        return {"error": f"无法凑够 {threshold:,} 战备，请检查数据"}

    best["efficiency"] = round(best["total_cr"] / max(best["total_price"], 1), 2)
    return best


def suggest_savings(loadout: dict, threshold: int):
    """Highlight items where CR > price (good deals)."""
    tips = []
    for item in loadout.get("items", []):
        if item["cr"] > item["price"]:
            diff = item["cr"] - item["price"]
            tips.append({
                "item": item["name"],
                "差价": diff,
                "说明": f"战备值 {item['cr']:,} 市场价仅 {item['price']:,}，白赚 {diff:,} 战备"
            })
    tips.sort(key=lambda x: x["差价"], reverse=True)
    return tips
