import pandas as pd
from datetime import datetime, timedelta
from src.data.ingester import stock_historical_data
from src.engine.features import compute_c_score
from src.data.cw_loader import get_cw_metrics, extract_underlying_from_cw

def run_backtest(symbol: str, days: int = 180) -> dict:
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    cw_metrics = get_cw_metrics(symbol)
    is_cw = cw_metrics.get("is_cw", False)
    base_symbol = extract_underlying_from_cw(symbol) if is_cw else symbol
    
    try:
        df = stock_historical_data(symbol=base_symbol, start_date=start_date, end_date=end_date, resolution="1D", type="stock")
    except Exception as e:
        return {"error": str(e)}
        
    if df is None or df.empty:
        return {"error": "Lỗi API dữ liệu lịch sử Cơ Sở từ TCBS."}
        
    # Trích xuất Động lượng lịch sử của Cổ phiếu Cơ Sở
    df['prev_close'] = df['close'].shift(1)
    df['base_momentum'] = (df['close'] - df['prev_close']) / df['prev_close'] * 100
    df = df.dropna()
    
    delta = cw_metrics.get('delta', 1.0)
    gearing = cw_metrics.get('gearing', 1.0)
    
    # Setup Biến số giao dịch
    initial_capital = 100000000 # Vốn gốc 100 Triệu VND
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = []
    
    # Khởi tạo giá Lập Phỏng (Giả đinh 1000đ khi IPO Chứng quyền)
    current_price = 1000.0 if is_cw else df.iloc[0]['close'] * 1000
    
    for index, row in df.iterrows():
        base_mom = row['base_momentum']
        
        # Mô phỏng Giá Trị Nội Tại Chứng Quyền (CW Theoretical Pricing)
        if is_cw:
            cw_momentum = base_mom * delta * gearing
            current_price = current_price * (1 + cw_momentum / 100)
            current_price = max(10.0, current_price) # Chống cháy tài khoản về âm
        else:
            current_price = row['close'] * 1000 # Mã Cơ sở chạy giá gốc
            
        spread = 1.5 if is_cw else 0.5 
        time_f = "SAFE" # Simulated 
        
        c_score = compute_c_score(spread, time_f, base_mom, delta, gearing)
        
        # Logic Vào / Ra Cốt lõi
        if c_score >= 66 and position == 0:
            position = capital // current_price
            capital -= position * current_price
            trades.append({"type": "BUY", "time": row['time'], "price": round(current_price, 0), "size": position})
            
        elif c_score < 50 and position > 0:
            capital += position * current_price
            trades.append({"type": "SELL", "time": row['time'], "price": round(current_price, 0), "size": position})
            position = 0
            
        current_equity = capital + (position * current_price)
        equity_curve.append({"time": row['time'], "equity": round(current_equity, 0)})
        
    # Tất toán cuối kỳ
    if position > 0:
        capital += position * current_price
        position = 0
        
    return {
        "symbol": symbol,
        "base_asset": base_symbol,
        "initial_capital": initial_capital,
        "final_capital": round(capital, 0),
        "total_return_pct": round((capital - initial_capital) / initial_capital * 100, 2),
        "total_trades": len(trades),
        "equity_curve": pd.DataFrame(equity_curve),
        "trades": pd.DataFrame(trades)
    }
