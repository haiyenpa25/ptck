import sqlite3
from pathlib import Path

def init_db(db_path: str = "cw_quant.db"):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS cw_config (
            symbol TEXT PRIMARY KEY,
            underlying TEXT,
            strike_price REAL,
            ratio REAL,
            expiry_date TEXT
        );
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            price REAL,
            volume INTEGER,
            bid1 REAL,
            ask1 REAL
        );
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            state TEXT,
            c_score REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
