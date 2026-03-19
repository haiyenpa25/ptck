import time
import sqlite3
import random
from src.core.database import init_db
from src.data.ingester import fetch_market_price
from src.engine.features import calculate_spread_factor, calculate_time_factor, compute_c_score
from src.engine.decision import evaluate_signals
from src.data.cw_loader import get_cw_metrics, get_all_symbols, extract_underlying_from_cw, load_app_settings
from alerts.telegram_bot import send_alert

DB_PATH = "cw_quant.db"

def save_market_data(conn, data):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO market_data (symbol, price, volume, bid1, ask1) VALUES (?, ?, ?, ?, ?)",
        (data.get("symbol"), data.get("price"), data.get("volume"), data.get("bid1"), data.get("ask1"))
    )
    conn.commit()

def save_signal(conn, symbol, state, c_score):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO signals (symbol, state, c_score) VALUES (?, ?, ?)",
        (symbol, state, c_score)
    )
    conn.commit()
    
def run_cycle():
    settings = load_app_settings()
    res = settings.get("resolution", "1D")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running Engine Cycle (Mode: {res})...")
    conn = sqlite3.connect(DB_PATH)
    active_watchlist = get_all_symbols()
    
    # 1. Nhóm các Chứng Quyền (CWs) theo Mã Cơ Sở (Base Underlying)
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
    for base, data_group in underlying_groups.items():
        try:
            base_data = fetch_market_price(base, resolution=res)
            if not base_data:
                continue
                
            # Lưu Data Cơ Sở chỉ để tham khảo (Không tạo Alert)
            save_market_data(conn, base_data)
            
            # Tính toán Động lượng thực tế (Thực chiến Intraday Momentum)
            base_price = base_data.get("price", 0)
            base_yest = base_data.get("yesterday_close", base_price)
            if base_yest > 0:
                base_momentum_pct = ((base_price - base_yest) / base_yest) * 100
            else:
                base_momentum_pct = 0.0
                
            # 3. Phân bổ C-Score cho các Chứng quyền con (Focus exclusively on small capital CWs)
            for cw_sym in data_group["cws"]:
                cw = get_cw_metrics(cw_sym)
                
                # TCBS Historical API blocks CW tickers. However, our V2 Strategy is purely Underlying-Driven!
                # We don't need the CW's live price. We calculate its momentum directly via Greeks.
                spread = 1.5 # Giả định chênh lệch Bid/Ask lý tưởng của CW là 1.5%
                time_f = "SAFE" # Fallback time factor
                
                # Tính C-Score dựa MẠNH VÀO Tín Hiệu Cơ Sở Dẫn Đường
                c_score = compute_c_score(spread, time_f, base_momentum_pct, cw['delta'], cw['gearing'])
                state = evaluate_signals(c_score)
                
                # Chỉ bắn tín hiệu cho CW 
                if state in ["PROBE", "CONFIRM", "MAX_SIZE"]:
                    save_signal(conn, cw_sym, state, float(c_score))
                    alert_msg = f"🔥 <b>CHỨNG QUYỀN V2 ALERT: {cw_sym}</b>\n"
                    alert_msg += f"Trạng thái: {state} | C-Score: {c_score:.1f}\n"
                    alert_msg += f"👉 Kéo từ Cơ Sở ({base}): {'+' if base_momentum_pct>0 else ''}{base_momentum_pct:.2f}%\n"
                    alert_msg += f"⚡ Gearing: {cw['gearing']}x | Delta: {cw['delta']}"
                    
                    send_alert(alert_msg)
                    
        except Exception as e:
            print(f"Error processing Pair {base}: {e}")
            
    conn.close()

if __name__ == "__main__":
    print("Starting CW-Centric Specialized Engine...")
    init_db(DB_PATH)
    while True:
        run_cycle()
        time.sleep(15)
