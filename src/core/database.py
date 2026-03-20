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
            underlying TEXT,
            state TEXT,
            c_score REAL,
            base_mome REAL,
            delta REAL,
            gearing REAL,
            strike_price REAL,
            ratio REAL,
            maturity_date TEXT,
            issuer TEXT,
            spread_score REAL,
            time_score REAL,
            mome_score REAL,
            cw_momentum_pct REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_price REAL NOT NULL,
            volume INTEGER NOT NULL,
            position_type TEXT NOT NULL,
            entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'OPEN',
            exit_price REAL,
            exit_time DATETIME,
            realized_pnl REAL
        );
    """)
    conn.commit()
    conn.close()
