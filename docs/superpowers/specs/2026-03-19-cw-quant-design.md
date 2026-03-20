# CW-Quant Local Trading Assistant - Design Specification

## 1. Goal
Build a local (Windows-first) quantitative trading assistant for Covered Warrants (CW). The system will ingest market data, calculate statistical edges (C-Score based on pricing and microstructure), manage state tracking (Probe, Confirm, Exit), and fire alerts via Telegram. It also includes a local Dashboard for monitoring.

## 2. Architecture & Constraints
- **Environment:** Local Windows machine.
- **Language:** Python 3.10+
- **Database:** SQLite (for zero-config local storage of ticks, OHLC, and signals).
- **UI:** Streamlit (fastest route for an MVP dashboard on Windows).
- **Alerts:** Telegram Bot.

## 3. Data Ingestion Approaches (Trade-offs)
Since the user is running this on a Local Windows machine, data acquisition is the biggest challenge for microscopic C-Score calculation.

*   **Approach A: `vnstock3` (Public API Scraper)**
    *   *Pros:* Free, pure Python, familiar to the user.
    *   *Cons:* Can have slight delays, lacks deep orderbook (L2) data for Microstructure C-Score.
*   **Approach B: Direct Broker API (TCBS/SSI/VND via reverse engineering)**
    *   *Pros:* True real-time, tick-by-tick orderbook.
    *   *Cons:* High maintenance, involves token refresh, risks being blocked.
*   **Approach C: Premium Data Feed (FireAnt / WiChart / v.v.)**
    *   *Pros:* Reliable and officially supported.
    *   *Cons:* Recurring cost.

**Recommendation:** We will proceed with **Approach A (`vnstock3`)** to build the engine architecture and validate the state machine. The Data Ingestion module will be abstracted so that the data source can be hot-swapped to Strategy B or C in Phase 3.

## 4. Component Breakdown (Design for Isolation)

1.  **`src/data/ingester.py`**: Fetches CW config and market data. Connects to SQLite `market_data` table.
2.  **`src/engine/features.py`**: A pure functional module. Takes raw prices and outputs factors: Spread, Time Risk (DTE), Delta-Adjusted Gearing.
3.  **`src/engine/decision.py`**: The State Machine. Evaluates the Features against the rules to transition states (IDLE -> PROBE -> CONFIRM -> EXIT).
4.  **`src/core/database.py`**: SQLite connection manager and Schema bootstrap.
5.  **`dashboard/app.py`**: Streamlit frontend. Reads strictly from SQLite (read-only) to display Heatmaps and latest signals.

## 5. Workflow
Data Ingester runs on an `apscheduler` loop (e.g., every 15 seconds) -> Saves to DB. 
Decision Engine runs immediately after -> Calculates C-Score -> If state changes, triggers Telegram Bot -> Saves state to `signals` table.
Dashboard automatically refreshes from the `signals` and `market_data` tables.
