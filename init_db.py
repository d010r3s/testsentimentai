import sqlite3
conn = sqlite3.connect("sentiment.db")
cur  = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS reviews(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 text TEXT, source TEXT, brand TEXT,
 created_at TEXT,
 sentiment TEXT, aspect TEXT
);
CREATE TABLE IF NOT EXISTS actions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 review_id INT REFERENCES reviews(id),
 reco TEXT, status TEXT DEFAULT 'NEW',
 created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit(); conn.close()
print("✅ DB ready")
