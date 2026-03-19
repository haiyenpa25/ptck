import time
import sqlite3
import random
from src.core.database import init_db
from src.data.ingester import fetch_market_price
from src.engine.features import calculate_spread_factor, calculate_time_factor, compute_c_score
from src.engine.decision import evaluate_signals
from alerts.telegram_bot import send_alert

# Mixture of Underlying Assets and actual CW codes (Covered Warrants)
WATCHLIST = ["FPT", "CFPT2305", "VNM", "CVNM2306", "HPG", "CHPG2331"]
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
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running ingestion cycle...")
    conn = sqlite3.connect(DB_PATH)
    
    for symbol in WATCHLIST:
        try:
            data = fetch_market_price(symbol)
            if not data:
                continue
                
            save_market_data(conn, data)
            
            # Calculate Quantitative Factors 
            spread = calculate_spread_factor(data["price"] * 0.99, data["price"] * 1.01) # fallback since realtime Bid/Ask is missing
            time_f = calculate_time_factor(random.randint(5, 45)) # simulated Days-to-Expiration
            momentum = random.uniform(-3.0, 3.0) # simulated 1-day momentum %
            
            # Compute actual C-Score from quantitative engine
            c_score = compute_c_score(spread, time_f, momentum)
            state = evaluate_signals(c_score)
            
            # If threshold crossed, send alert and save signal
            if state in ["PROBE", "CONFIRM", "MAX_SIZE"]:
                save_signal(conn, symbol, state, round(c_score, 2))
                send_alert(f"🚨 SIGNAL ALERT 🚨\nSymbol: {symbol}\nState: {state}\nC-Score: {c_score:.2f}")
                
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            
    conn.close()

if __name__ == "__main__":
    print("Starting CW-Quant Main Scheduler Loop...")
    init_db(DB_PATH)
    while True:
        run_cycle()
        time.sleep(15) # run every 15 seconds for testing purposes
