# -*- coding: utf-8 -*-
import os, sqlite3, json, time
from appdirs import user_data_dir

APP_NAME = "clipboard_sequencer"
APP_AUTHOR = "local"

def data_dir() -> str:
    d = user_data_dir(APP_NAME, APP_AUTHOR)
    os.makedirs(d, exist_ok=True)
    return d

def cache_img_dir() -> str:
    d = os.path.join(os.path.expanduser("~"), f".{APP_NAME}", "cache", "images")
    os.makedirs(d, exist_ok=True)
    return d

def db_path() -> str:
    return os.path.join(data_dir(), "data.db")

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

SCHEMA = '''
CREATE TABLE IF NOT EXISTS sessions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at INTEGER NOT NULL,
  closed_at INTEGER
);
CREATE TABLE IF NOT EXISTS items(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER,
  type TEXT NOT NULL,        -- text|image|files
  text TEXT,
  image_path TEXT,
  paths_json TEXT,           -- json list for files
  count INTEGER DEFAULT 1,
  status TEXT NOT NULL,      -- active|used
  pinned INTEGER DEFAULT 0,
  edited INTEGER DEFAULT 0,
  note TEXT,
  created_at INTEGER NOT NULL,
  last_used_at INTEGER,
  FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS collections(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS collection_map(
  collection_id INTEGER NOT NULL,
  item_id INTEGER NOT NULL,
  PRIMARY KEY(collection_id, item_id),
  FOREIGN KEY(collection_id) REFERENCES collections(id) ON DELETE CASCADE,
  FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
);
'''

def init_db():
    conn = connect()
    with conn:
        conn.executescript(SCHEMA)
        cur = conn.execute("SELECT id FROM collections WHERE name=?", ("favorites",))
        if cur.fetchone() is None:
            conn.execute("INSERT INTO collections(name) VALUES (?)", ("favorites",))
        cur = conn.execute("SELECT id FROM sessions WHERE closed_at IS NULL ORDER BY id DESC LIMIT 1")
        if cur.fetchone() is None:
            conn.execute("INSERT INTO sessions(started_at) VALUES (?)", (int(time.time()),))
    conn.close()

def get_current_session_id(conn: sqlite3.Connection) -> int:
    cur = conn.execute("SELECT id FROM sessions WHERE closed_at IS NULL ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO sessions(started_at) VALUES (?)", (int(time.time()),))
    return cur.lastrowid

# ---------- add items ----------
def add_text_item(text: str, duplicate_policy: str):
    conn = connect()
    try:
        sid = get_current_session_id(conn)
        ts = int(time.time())
        if duplicate_policy == "count":
            cur = conn.execute("SELECT id, count FROM items WHERE type='text' AND text=? ORDER BY id DESC LIMIT 1", (text,))
            row = cur.fetchone()
            if row:
                with conn:
                    conn.execute("UPDATE items SET count=? WHERE id=?", (row[1]+1, row[0]))
                return row[0]
        with conn:
            cur = conn.execute(
                "INSERT INTO items(session_id, type, text, count, status, created_at) VALUES (?,?,?,?,?,?)",
                (sid, "text", text, 1, "active", ts)
            )
            return cur.lastrowid
    finally:
        conn.close()

def add_image_item(image_path: str):
    conn = connect()
    try:
        sid = get_current_session_id(conn)
        ts = int(time.time())
        with conn:
            cur = conn.execute(
                "INSERT INTO items(session_id, type, image_path, status, created_at) VALUES (?,?,?,?,?)",
                (sid, "image", image_path, "active", ts)
            )
            return cur.lastrowid
    finally:
        conn.close()

def add_files_item(paths: list[str]):
    conn = connect()
    try:
        sid = get_current_session_id(conn)
        ts = int(time.time())
        with conn:
            cur = conn.execute(
                "INSERT INTO items(session_id, type, paths_json, status, created_at) VALUES (?,?,?,?,?)",
                (sid, "files", json.dumps(paths, ensure_ascii=False), "active", ts)
            )
            return cur.lastrowid
    finally:
        conn.close()

# ---------- list / status ----------
def list_items_all(limit=500):
    conn = connect()
    try:
        cur = conn.execute("SELECT * FROM items ORDER BY id ASC LIMIT ?", (limit,))
        return cur.fetchall()
    finally:
        conn.close()

def list_favorites(limit=500):
    conn = connect()
    try:
        cur = conn.execute("""
        SELECT i.* FROM items i
        JOIN collection_map m ON m.item_id=i.id
        JOIN collections c ON c.id=m.collection_id AND c.name='favorites'
        ORDER BY i.id ASC LIMIT ?
        """, (limit,))
        return cur.fetchall()
    finally:
        conn.close()

def set_item_used(item_id: int):
    conn = connect()
    try:
        ts = int(time.time())
        with conn:
            conn.execute("UPDATE items SET status='used', last_used_at=? WHERE id=?", (ts, item_id))
    finally:
        conn.close()

def set_item_active(item_id: int):
    conn = connect()
    try:
        with conn:
            conn.execute("UPDATE items SET status='active' WHERE id=?", (item_id,))
    finally:
        conn.close()

def delete_items(ids: list[int]):
    if not ids:
        return
    conn = connect()
    try:
        with conn:
            conn.executemany("DELETE FROM items WHERE id=?", [(i,) for i in ids])
    finally:
        conn.close()

# ---------- favorites ----------
def _favorites_id(conn: sqlite3.Connection) -> int:
    r = conn.execute("SELECT id FROM collections WHERE name='favorites'").fetchone()
    return r[0]

def set_favorite(item_id: int, fav: bool):
    conn = connect()
    try:
        cid = _favorites_id(conn)
        with conn:
            if fav:
                conn.execute("INSERT OR IGNORE INTO collection_map(collection_id, item_id) VALUES (?,?)", (cid, item_id))
            else:
                conn.execute("DELETE FROM collection_map WHERE collection_id=? AND item_id=?", (cid, item_id))
    finally:
        conn.close()

def is_favorite(item_id: int) -> bool:
    conn = connect()
    try:
        cid = _favorites_id(conn)
        r = conn.execute("SELECT 1 FROM collection_map WHERE collection_id=? AND item_id=? LIMIT 1", (cid, item_id)).fetchone()
        return r is not None
    finally:
        conn.close()
