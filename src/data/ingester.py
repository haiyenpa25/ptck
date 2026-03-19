import pandas as pd
from datetime import datetime, timedelta

try:
    from vnstock import stock_historical_data
except Exception as e:
    global_import_error = str(e)
    # Fallback/Mock if not installed yet
    def stock_historical_data(*args, **kwargs):
        raise NotImplementedError(f"vnstock import failed: {global_import_error}")

def fetch_market_price(symbol: str, resolution: str = "1D") -> dict:
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # TCBS intraday requires tight window to prevent huge payloads
        if resolution in ["1", "5", "15", "30", "1H"]:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        df = stock_historical_data(symbol=symbol, start_date=start_date, end_date=end_date, resolution=resolution, type="stock")
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            last_close = df.iloc[-2]['close'] if len(df) > 1 else latest['close']
            return {
                "symbol": symbol,
                "price": float(latest['close']) * 1000,
                "yesterday_close": float(last_close) * 1000,
                "volume": int(latest.get('volume', 0)),
                "bid1": 0.0, # Placeholder
                "ask1": 0.0  # Placeholder
            }
        return {}
    except Exception as e:
        print(f"fetch error for {symbol}: {e}")
        return {}
