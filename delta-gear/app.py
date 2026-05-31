"""DeltaGear — 三角洲行动最低成本卡战备计算器"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

import database as db
from optimizer import calculate, suggest_savings
from price_fetcher import refresh_prices

DATA_MODE = "🟢 实时"

@st.cache_data(ttl=600)
def get_cached_prices():
    """Cache price data for 10 minutes."""
    return db.get_all_latest_prices()

@st.cache_data(ttl=600)
def get_cached_items():
    return db.get_all_items()

@st.cache_data(ttl=600)
def get_cached_maps():
    return db.get_all_maps()

st.set_page_config(
    page_title="DeltaGear — 卡战备计算器",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

# ── Sidebar ──
with st.sidebar:
    st.title("🎯 DeltaGear")
    st.caption("三角洲行动 · 低成本卡战备")

    item_count = db.item_count()
    map_count = len(get_cached_maps())
    col1, col2, col3 = st.columns(3)
    col1.metric("装备", item_count)
    col2.metric("地图", map_count)
    col3.metric("数据", DATA_MODE)

    st.divider()
    page = st.radio(
        "导航",
        ["🔧 DIY配装", "📊 物价总览", "✏️ 战备录入", "🗺 地图门槛", "📈 价格趋势"],
        label_visibility="collapsed",
    )

    st.divider()
    if st.button("🔄 刷新物价", use_container_width=True):
        with st.spinner("抓取交易行实时价格..."):
            result = refresh_prices("live")
            if "error" in result:
                st.warning(result["error"])
            else:
                st.cache_data.clear()
                st.success(f"已更新 {result['saved']} 条价格 — {result['source']}")

# ══════════════════════════════════════════════════════════════
# 计算配装（首页）
# ══════════════════════════════════════════════════════════════

if page == "🔧 DIY配装":
    st.title("🔧 自由搭配配装计算")

    prices = get_cached_prices()
    if not prices:
        st.warning("暂无数据，请先刷新物价")
        st.stop()

    # Build lookup
    items_by_slot = {}
    for p in prices:
        slot = p["slot"]
        if slot not in items_by_slot:
            items_by_slot[slot] = []
        items_by_slot[slot].append(p)

    for slot in items_by_slot:
        items_by_slot[slot].sort(key=lambda x: x["name"])

    # ── Selection UI ──
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("选择装备")

        # Weapon
        weapon_names = ["无"] + sorted(set(p["name"] for p in items_by_slot.get("武器", [])))
        selected_weapon_name = st.selectbox("🔫 主武器", weapon_names, key="diy_weapon")
        selected_weapon = None
        if selected_weapon_name != "无":
            selected_weapon = next((p for p in prices if p["name"] == selected_weapon_name), None)

        # Attachments (multiple)
        st.caption("🔩 配件（可多选）")
        att_names = sorted(set(p["name"] for p in items_by_slot.get("配件", [])))
        att_container = st.container(height=250)
        with att_container:
            selected_att_names = []
            for aname in att_names:
                if st.checkbox(aname, key=f"diy_att_{aname}"):
                    selected_att_names.append(aname)

        selected_atts = [p for p in prices if p["name"] in selected_att_names and p["slot"] == "配件"]

        # Armor slots
        c1, c2 = st.columns(2)
        with c1:
            helmet_names = ["无"] + sorted(set(p["name"] for p in items_by_slot.get("头盔", [])))
            selected_helmet_name = st.selectbox("🪖 头盔", helmet_names, key="diy_helmet")

            armor_names = ["无"] + sorted(set(p["name"] for p in items_by_slot.get("护甲", [])))
            selected_armor_name = st.selectbox("🛡 护甲", armor_names, key="diy_armor")

        with c2:
            bp_names = ["无"] + sorted(set(p["name"] for p in items_by_slot.get("背包", [])))
            selected_bp_name = st.selectbox("🎒 背包", bp_names, key="diy_bp")

            rig_names = ["无"] + sorted(set(p["name"] for p in items_by_slot.get("胸挂", [])))
            selected_rig_name = st.selectbox("🎽 胸挂", rig_names, key="diy_rig")

    # ── Summary ──
    with col_right:
        st.subheader("💰 计算结果")

        # Collect selected gear
        gear_items = []
        if selected_weapon:
            gear_items.append(("武器", selected_weapon))
        for a in selected_atts:
            gear_items.append(("配件", a))
        if selected_helmet_name != "无":
            gear_items.append(("头盔", next(p for p in prices if p["name"] == selected_helmet_name)))
        if selected_armor_name != "无":
            gear_items.append(("护甲", next(p for p in prices if p["name"] == selected_armor_name)))
        if selected_bp_name != "无":
            gear_items.append(("背包", next(p for p in prices if p["name"] == selected_bp_name)))
        if selected_rig_name != "无":
            gear_items.append(("胸挂", next(p for p in prices if p["name"] == selected_rig_name)))

        total_price = sum(it[1].get("price") or 0 for it in gear_items)
        total_cr = sum(it[1]["combat_readiness"] for it in gear_items)

        st.metric("💰 总市场价", f"{total_price:,} 哈夫币")
        st.metric("🎯 总战备值", f"{total_cr:,}")
        delta = total_cr - total_price
        st.metric("📊 差价", f"{delta:,}", delta=f"+{delta:,}" if delta > 0 else f"{delta:,}")

        st.divider()
        st.subheader("🗺 可进地图")

        maps = get_cached_maps()
        for m in maps:
            can_enter = total_cr >= m["threshold"]
            icon = "✅" if can_enter else "❌"
            gap = total_cr - m["threshold"]
            if can_enter:
                st.success(f"{icon} {m['name']} {m['difficulty']} — 超出 {gap:,}")
            else:
                st.error(f"{icon} {m['name']} {m['difficulty']} — 差 {abs(gap):,}")

        # Equipment list
        st.divider()
        st.subheader("📋 装备清单")
        if gear_items:
            rows = []
            for slot, item in gear_items:
                rows.append({
                    "部位": slot,
                    "装备": item["name"],
                    "市场价": f"{item.get('price') or 0:,}",
                    "战备值": f"{item['combat_readiness']:,}",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("尚未选择装备")

# ══════════════════════════════════════════════════════════════
# 物价总览
# ══════════════════════════════════════════════════════════════

elif page == "📊 物价总览":
    st.title("📊 物价总览")

    prices = get_cached_prices()
    if not prices:
        st.warning("暂无价格数据，请先点击侧边栏「刷新物价」")
        st.stop()

    from collections import defaultdict

    # Filter by slot
    slots = ["全部"] + sorted(set(p.get("slot", "") for p in prices))
    selected_slot = st.selectbox("筛选部位", slots)

    # Filter
    filtered = [p for p in prices if selected_slot == "全部" or p["slot"] == selected_slot]

    # Group by category
    items_by_cat = defaultdict(list)
    for p in filtered:
        items_by_cat[p["category"]].append(p)

    st.caption(f"共 {len(filtered)} 件装备，{len(items_by_cat)} 个分类 | 效率比 = 战备值÷市场价，越高越划算")

    # Display each category in its own expander
    for cat in sorted(items_by_cat.keys()):
        items = items_by_cat[cat]
        rows = []
        for p in items:
            price = p.get("price") or 0
            cr = p["combat_readiness"]
            efficiency = round(cr / max(price, 1), 2) if price > 0 else 0
            rows.append({
                "名称": p["name"],
                "部位": p["slot"],
                "市场价": price,
                "战备值": cr,
                "效率比": efficiency,
                "更新时间": str(p.get("recorded_at", ""))[:16] if p.get("recorded_at") else "无",
            })
        rows.sort(key=lambda x: x["效率比"], reverse=True)
        df = pd.DataFrame(rows)

        with st.expander(f"📦 {cat}（{len(rows)} 件）"):
            st.dataframe(df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# 战备录入
# ══════════════════════════════════════════════════════════════

elif page == "✏️ 战备录入":
    st.title("✏️ 战备值录入")

    prices = get_cached_prices()
    if not prices:
        st.warning("暂无数据")
        st.stop()

    from collections import defaultdict

    # Filter
    slot_filter = st.selectbox("筛选部位", ["全部"] + sorted(set(p.get("slot", "") for p in prices)), key="cr_slot_filter")
    search = st.text_input("搜索装备名", key="cr_search")

    filtered = [p for p in prices if (slot_filter == "全部" or p["slot"] == slot_filter)]
    if search:
        filtered = [p for p in filtered if search.lower() in p.get("name", "").lower()]

    # Group by category
    items_by_cat = defaultdict(list)
    for p in filtered:
        items_by_cat[p["category"]].append(p)

    st.caption(f"共 {len(filtered)} 件，{len(items_by_cat)} 个分类 | 🟢 已验证 | ⚪ 估算值")

    # Display each category in its own expander
    for cat in sorted(items_by_cat.keys()):
        items = items_by_cat[cat]
        with st.expander(f"📦 {cat}（{len(items)} 件）"):
            for p in items:
                price = p.get("price") or 0
                cr = p["combat_readiness"]
                verified = p.get("notes") == "verified"
                indicator = "🟢" if verified else "⚪"

                col_info, col_input, col_actions = st.columns([3, 2, 2])
                with col_info:
                    st.markdown(f"{indicator} **{p['name']}**  \n"
                                f"<small>市场价: {price:,} | 部位: {p['slot']}</small>",
                                unsafe_allow_html=True)
                with col_input:
                    new_cr = st.number_input(
                        "战备值",
                        value=cr,
                        step=100,
                        key=f"cr_{p['id']}",
                        label_visibility="collapsed",
                    )
                with col_actions:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("💾 保存", key=f"save_cr_{p['id']}"):
                            conn = db.get_db()
                            conn.execute("UPDATE items SET combat_readiness=?, notes='verified' WHERE id=?", (new_cr, p["id"]))
                            conn.commit()
                            conn.close()
                            st.cache_data.clear()
                            st.success("已保存")
                            st.rerun()
                    with c2:
                        if st.button("🔄 重置", key=f"reset_cr_{p['id']}"):
                            conn = db.get_db()
                            est = int((price or 0) * 1.05)
                            conn.execute("UPDATE items SET combat_readiness=?, notes='' WHERE id=?", (est, p["id"]))
                            conn.commit()
                            conn.close()
                            st.cache_data.clear()
                            st.rerun()

# ══════════════════════════════════════════════════════════════
# 地图门槛
# ══════════════════════════════════════════════════════════════

elif page == "🗺 地图门槛":
    st.title("🗺 地图门槛")

    maps = get_cached_maps()
    if not maps:
        st.info("无地图数据")
    else:
        rows = [{"地图": m["name"], "难度": m["difficulty"], "战备门槛": f"{m['threshold']:,}"} for m in maps]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📝 说明")
    st.markdown("""
    - **战备值** = 你身上装备的「装备价值」总和
    - **药品、弹药不计入战备值**（只要能塞进安全箱的都不算）
    - 必须达到门槛才能进入对应地图/难度
    - 核心思路：找「战备值虚高但市场价低」的装备（如破损头盔、特定配件）
    """)

# ══════════════════════════════════════════════════════════════
# 价格趋势
# ══════════════════════════════════════════════════════════════

elif page == "📈 价格趋势":
    st.title("📈 价格趋势")

    items = get_cached_items()
    if not items:
        st.info("暂无数据")
        st.stop()

    selected_name = st.selectbox("选择装备", [it["name"] for it in items])
    selected_item = next((it for it in items if it["name"] == selected_name), None)

    if selected_item:
        history = db.get_price_history(selected_item["id"], limit=60)
        if history:
            df = pd.DataFrame(history)
            df["recorded_at"] = pd.to_datetime(df["recorded_at"])
            df = df.set_index("recorded_at")

            fig = px.line(df, y="price", title=f"{selected_name} 价格趋势")
            fig.update_layout(yaxis_title="价格 (哈夫币)", xaxis_title="时间")
            st.plotly_chart(fig, use_container_width=True)

            # Stats
            prices_list = [h["price"] for h in history]
            c1, c2, c3 = st.columns(3)
            c1.metric("当前", f"{prices_list[-1]:,.0f}")
            c2.metric("最低", f"{min(prices_list):,.0f}")
            c3.metric("最高", f"{max(prices_list):,.0f}")
        else:
            st.info("暂无该装备的价格历史，请先刷新物价")
