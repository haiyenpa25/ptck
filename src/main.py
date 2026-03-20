import time
import sqlite3
import random
from src.core.database import init_db
from src.data.ingester import fetch_market_price
from src.engine.features import calculate_spread_factor, calculate_time_factor, compute_c_score
from src.engine.decision import evaluate_signals
from src.data.cw_loader import get_cw_metrics, get_all_symbols, extract_underlying_from_cw
from src.data.settings_loader import load_app_settings
from alerts.telegram_bot import send_alert

DB_PATH = "cw_quant.db"

def save_market_data(conn, data):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO market_data (symbol, price, volume, bid1, ask1) VALUES (?, ?, ?, ?, ?)",
        (data.get("symbol"), data.get("price"), data.get("volume"), data.get("bid1"), data.get("ask1"))
    )
    conn.commit()

METADATA_CACHE = {}

def save_signal(conn, symbol, state, c_breakdown, underlying=None, base_mome=0.0, delta=0.0, gearing=0.0, meta=None):
    cursor = conn.cursor()
    meta = meta or {}
    cursor.execute(
        """INSERT INTO signals (
            symbol, state, c_score, underlying, base_mome, delta, gearing,
            strike_price, ratio, maturity_date, issuer,
            spread_score, time_score, mome_score, cw_momentum_pct
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            symbol, state, c_breakdown['total'], underlying, base_mome, delta, gearing,
            meta.get('strike_price', 0), meta.get('ratio', '1:1'), meta.get('maturity_date', 'N/A'), meta.get('issuer', 'Unknown'),
            c_breakdown['spread_score'], c_breakdown['time_score'], c_breakdown['mome_score'], c_breakdown['cw_mome']
        )
    )
    conn.commit()
    
def run_cycle():
    settings = load_app_settings()
    res = settings.get("resolution", "1D")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running Engine Cycle (Mode: {res})...")
    conn = sqlite3.connect(DB_PATH)
    active_watchlist = get_all_symbols()
    
    # 1. Nhóm các Chứng Quyền (CWs) theo Mã Cơ Sở
    underlying_groups = {} 
    for symbol in active_watchlist:
        cw_metrics = get_cw_metrics(symbol)
        if cw_metrics.get('is_cw'):
            base = extract_underlying_from_cw(symbol)
            if base not in underlying_groups:
                underlying_groups[base] = {"base": base, "cws": []}
            underlying_groups[base]["cws"].append(symbol)
        else:
            base = symbol
            if base not in underlying_groups:
                underlying_groups[base] = {"base": base, "cws": []}
                
    # 2. Xử lý từng Nhóm Mã Cơ Sở
    from src.data.cw_loader import fetch_warrant_metadata
    for base, data_group in underlying_groups.items():
        try:
            base_data = fetch_market_price(base, resolution=res)
            if not base_data:
                continue
            
            save_market_data(conn, base_data)
            base_price = base_data.get("price", 0)
            base_yest = base_data.get("yesterday_close", base_price)
            base_momentum_pct = ((base_price - base_yest) / base_yest) * 100 if base_yest > 0 else 0.0
                
            # 3. Phân bổ C-Score cho các Chứng quyền con
            for cw_sym in data_group["cws"]:
                cw = get_cw_metrics(cw_sym)
                spread = 1.5 
                time_f = "SAFE" 
                
                # Tính C-Score breakdown
                c_breakdown = compute_c_score(spread, time_f, base_momentum_pct, cw['delta'], cw['gearing'])
                state = evaluate_signals(c_breakdown['total'])
                
                # Fetch metadata if not in cache
                if cw_sym not in METADATA_CACHE:
                    METADATA_CACHE[cw_sym] = fetch_warrant_metadata(cw_sym)
                meta = METADATA_CACHE[cw_sym]
                
                if state in ["PROBE", "CONFIRM", "MAX_SIZE"]:
                    save_signal(conn, cw_sym, state, c_breakdown, base, float(base_momentum_pct), float(cw['delta']), float(cw['gearing']), meta)
                    
                    alert_msg = f"🔥 <b>SIGNAL: {cw_sym}</b> ({state})\n"
                    alert_msg += f"Score: {c_breakdown['total']:.1f} | Under: {base} ({base_momentum_pct:+.2f}%)\n"
                    alert_msg += f"Exp: {meta.get('maturity_date', 'N/A')} | Gear: {cw['gearing']}x"
                    send_alert(alert_msg)
                    
        except Exception as e:
            print(f"Error processing {base}: {e}")
            
    conn.close()

if __name__ == "__main__":
    print("Starting CW-Centric Specialized Engine...")
    init_db(DB_PATH)
    while True:
        run_cycle()
        time.sleep(15)
