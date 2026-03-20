# CW-Quant Data Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 1 Data Ingestion and SQLite bootstrapping for the local CW-Quant system using `vnstock3`.

**Architecture:** A Python scheduler that pulls market data using `vnstock3`, parses it into a standard format, and saves it to a local SQLite database designed for rapid reads by the Streamlit dashboard.

**Tech Stack:** Python 3.10+, SQLite, `vnstock3`, `pandas`, `pytest`

---

### Task 1: Initialize Project & Database Schema

**Files:**
- Create: `src/core/database.py`
- Create: `tests/core/test_database.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/core/test_database.py
import sqlite3
import os
from src.core.database import init_db

def test_init_db_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(str(db_path))
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert "market_data" in tables
    assert "signals" in tables
    assert "cw_config" in tables
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_database.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src'"

- [ ] **Step 3: Write minimal implementation**

```python
# src/core/database.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_database.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/database.py tests/core/test_database.py
git commit -m "feat: initialize sqlite database schema for cw-quant"
```

---

### Task 2: Data Ingestion Wrapper for vnstock3

**Files:**
- Create: `src/data/ingester.py`
- Create: `tests/data/test_ingester.py`

- [ ] **Step 1: Write the failing mock test**

```python
# tests/data/test_ingester.py
from src.data.ingester import fetch_market_price
from unittest.mock import patch

@patch('src.data.ingester.stock_historical_data')
def test_fetch_market_price(mock_historical):
    import pandas as pd
    # Mocking vnstock3 response
    mock_historical.return_value = pd.DataFrame({
        'time': ['2026-03-19'], 'open': [100], 'high': [105], 'low': [99], 'close': [102], 'volume': [1000]
    })
    
    result = fetch_market_price('VNM')
    assert result['symbol'] == 'VNM'
    assert result['price'] == 102
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/data/test_ingester.py -v`
Expected: FAIL 

- [ ] **Step 3: Write minimal implementation**

```python
# src/data/ingester.py
import pandas as pd
try:
    from vnstock3 import stock_historical_data
except ImportError:
    # Fallback/Mock if not installed yet
    def stock_historical_data(*args, **kwargs):
        raise NotImplementedError("vnstock3 not installed")

def fetch_market_price(symbol: str) -> dict:
    # In a real environment, we might use a tick-data endpoint.
    # For MVP, we extract the latest close price from history.
    try:
        df = stock_historical_data(symbol, "1D", "2026-01-01", "2026-12-31") # Example dates
        if not df.empty:
            latest = df.iloc[-1]
            return {
                "symbol": symbol,
                "price": float(latest['close']),
                "volume": int(latest.get('volume', 0)),
                "bid1": 0.0, # Placeholder
                "ask1": 0.0  # Placeholder
            }
        return {}
    except Exception as e:
        return {}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/data/test_ingester.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/data/ingester.py tests/data/test_ingester.py
git commit -m "feat: create vnstock3 data ingestion wrapper"
```
