"""SQLite database layer for DeltaGear."""
import sqlite3
from datetime import datetime, timezone

DB_PATH = "deltagear.db"

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            slot TEXT NOT NULL,
            combat_readiness INTEGER NOT NULL DEFAULT 0,
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
            price REAL NOT NULL,
            recorded_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS maps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            threshold INTEGER NOT NULL,
            UNIQUE(name, difficulty)
        );

        CREATE TABLE IF NOT EXISTS loadouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            map_id INTEGER NOT NULL REFERENCES maps(id),
            total_price REAL NOT NULL,
            total_cr INTEGER NOT NULL,
            items_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_prices_item_time ON prices(item_id, recorded_at);
        CREATE INDEX IF NOT EXISTS idx_items_slot ON items(slot);
    """)
    conn.commit()
    conn.close()

# ── Items ──
def get_all_items():
    conn = get_db()
    rows = conn.execute("SELECT * FROM items ORDER BY category, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_items_by_slot(slot: str):
    conn = get_db()
    rows = conn.execute("SELECT * FROM items WHERE slot=? ORDER BY name", (slot,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_item(name: str, category: str, slot: str, combat_readiness: int, notes: str = ""):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO items (name, category, slot, combat_readiness, notes) VALUES (?,?,?,?,?)",
        (name, category, slot, combat_readiness, notes),
    )
    conn.commit()
    conn.close()

def item_count():
    conn = get_db()
    n = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    conn.close()
    return n

# ── Prices ──
def save_price(item_id: int, price: float):
    conn = get_db()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO prices (item_id, price, recorded_at) VALUES (?,?,?)", (item_id, price, now))
    conn.commit()
    conn.close()

def get_latest_price(item_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT price, recorded_at FROM prices WHERE item_id=? ORDER BY recorded_at DESC LIMIT 1",
        (item_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_price_history(item_id: int, limit: int = 30):
    conn = get_db()
    rows = conn.execute(
        "SELECT price, recorded_at FROM prices WHERE item_id=? ORDER BY recorded_at DESC LIMIT ?",
        (item_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows][::-1]

def get_all_latest_prices():
    conn = get_db()
    rows = conn.execute("""
        SELECT i.id, i.name, i.category, i.slot, i.combat_readiness,
               p.price, p.recorded_at
        FROM items i
        LEFT JOIN (
            SELECT item_id, price, recorded_at
            FROM prices
            WHERE (item_id, recorded_at) IN (
                SELECT item_id, MAX(recorded_at) FROM prices GROUP BY item_id
            )
        ) p ON i.id = p.item_id
        ORDER BY i.category, i.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Maps ──
def get_all_maps():
    conn = get_db()
    rows = conn.execute("SELECT * FROM maps ORDER BY threshold").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_map(name: str, difficulty: str, threshold: int):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO maps (name, difficulty, threshold) VALUES (?,?,?)",
        (name, difficulty, threshold),
    )
    conn.commit()
    conn.close()

# ── Loadouts (cache) ──
def save_loadout(map_id: int, total_price: float, total_cr: int, items: list):
    import json
    conn = get_db()
    conn.execute(
        "INSERT INTO loadouts (map_id, total_price, total_cr, items_json) VALUES (?,?,?,?)",
        (map_id, total_price, total_cr, json.dumps(items, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

def get_latest_loadout(map_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM loadouts WHERE map_id=? ORDER BY created_at DESC LIMIT 1",
        (map_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
