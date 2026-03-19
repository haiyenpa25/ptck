import pandas as pd
from datetime import datetime, timedelta
from src.data.ingester import stock_historical_data
from src.engine.features import compute_c_score
from src.data.cw_loader import get_cw_metrics

def run_backtest(symbol: str, days: int = 180) -> dict:
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    try:
        df = stock_historical_data(symbol=symbol, start_date=start_date, end_date=end_date, resolution="1D", type="stock")
    except Exception as e:
        return {"error": str(e)}
        
    if df is None or df.empty:
        return {"error": "No data returned from vnstock"}
        
    # Variables for simulation
    initial_capital = 100000000 # 100M VND
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = []
    
    # Calculate daily momentum required by C-Score Engine
    df['prev_close'] = df['close'].shift(1)
    df['momentum'] = (df['close'] - df['prev_close']) / df['prev_close'] * 100
    df = df.dropna()
    
    # Load parameters (default 1.0 for UA if not configured)
    cw_metrics = get_cw_metrics(symbol)
    delta = cw_metrics['delta']
    gearing = cw_metrics['gearing']
    
    for index, row in df.iterrows():
        # Simulated standard factors for history
        spread = 1.0 
        time_f = "SAFE"
        
        c_score = compute_c_score(spread, time_f, row['momentum'], delta, gearing)
        price = row['close']
        
        # Logic: 
        # C-Score >= 66 means CONFIRM or MAX_SIZE -> BUY Signal
        # C-Score < 50 means IDLE -> SELL Signal
        if c_score >= 66 and position == 0:
            position = capital // price
            capital -= position * price
            trades.append({"type": "BUY", "time": row['time'], "price": price, "size": position})
            
        elif c_score < 50 and position > 0:
            capital += position * price
            trades.append({"type": "SELL", "time": row['time'], "price": price, "size": position})
            position = 0
            
        current_equity = capital + (position * price)
        equity_curve.append({"time": row['time'], "equity": current_equity})
        
    # Mark to market and close all positions at the very end
    if position > 0:
        capital += position * df.iloc[-1]['close']
        position = 0
        
    return {
        "symbol": symbol,
        "initial_capital": initial_capital,
        "final_capital": capital,
        "total_return_pct": round((capital - initial_capital) / initial_capital * 100, 2),
        "total_trades": len(trades),
        "equity_curve": pd.DataFrame(equity_curve),
        "trades": pd.DataFrame(trades)
    }
