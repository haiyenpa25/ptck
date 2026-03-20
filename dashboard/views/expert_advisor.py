import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.data.ingester import stock_historical_data

def render_expert_advisor():
    st.header("🔮 Cố Vấn Tự Động (Dành Cho Nhà Đầu Tư Mới Khởi Đầu)")
    st.markdown("""
    Cỗ máy AI này đang dùng **mật mã phân tích của các Quỹ Đầu Tư** (đọc 6 lớp biểu đồ: Xu hướng, Động lượng, Dòng tiền...) 
    nhưng sẽ **giải thích cho bạn bằng ngôn ngữ đời thường, bình dân nhất**. Bạn không cần phải giỏi toán hay thuộc biểu đồ, hãy đọc kỹ những diễn giải bên dưới!
    """)
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        target_sym = st.text_input("🔍 Gõ Mã Cổ Phiếu Bạn Đang Quan Tâm (VD: FPT, HPG, SSI):", "FPT").upper()
        if st.button("🧠 Yêu Cầu Chuyên Gia Chẩn Đoán", use_container_width=True):
            st.session_state['expert_run'] = target_sym
            
    if 'expert_run' in st.session_state:
        sym = st.session_state['expert_run']
        
        with st.spinner(f"Đang phân tích sổ xố dĩ vãng 6 tháng qua của {sym} để tìm ra quy luật..."):
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
            
            try:
                df = stock_historical_data(symbol=sym, start_date=start_date, end_date=end_date, resolution="1D", type="stock")
            except Exception as e:
                st.error(f"Lỗi truy xuất dữ liệu: {e}")
                return
                
            if df is None or len(df) < 50:
                st.warning(f"Dữ liệu của {sym} quá ít. Hãy chọn một mã Bluechip (ví dụ: VNM, SSI, HPG) để hệ thống hoạt động tốt nhất.")
                return
                
            # ==========================================
            # 1. CORE MATH ENGINE (Vectorization)
            # ==========================================
            df['Prev_H'] = df['high'].shift(1)
            df['Prev_L'] = df['low'].shift(1)
            df['Prev_C'] = df['close'].shift(1)

            df['SMA_20'] = df['close'].rolling(window=20).mean()
            df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
            df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
            
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['Hist'] = df['MACD'] - df['Signal']  # MACD Histogram

            # ADX
            df['TR'] = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['Prev_C']), abs(df['low'] - df['Prev_C'])))
            df['+DM'] = np.where((df['high'] - df['Prev_H'] > df['Prev_L'] - df['low']) & (df['high'] - df['Prev_H'] > 0), df['high'] - df['Prev_H'], 0)
            df['-DM'] = np.where((df['Prev_L'] - df['low'] > df['high'] - df['Prev_H']) & (df['Prev_L'] - df['low'] > 0), df['Prev_L'] - df['low'], 0)
            df['TR_14'] = df['TR'].ewm(alpha=1/14, adjust=False).mean()
            df['+DM_14'] = df['+DM'].ewm(alpha=1/14, adjust=False).mean()
            df['-DM_14'] = df['-DM'].ewm(alpha=1/14, adjust=False).mean()
            df['+DI'] = 100 * (df['+DM_14'] / (df['TR_14'] + 1e-10))
            df['-DI'] = 100 * (df['-DM_14'] / (df['TR_14'] + 1e-10))
            df['DX'] = 100 * abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'] + 1e-10)
            df['ADX_14'] = df['DX'].ewm(alpha=1/14, adjust=False).mean()

            # RSI & Stochastic
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            df['RSI_14'] = 100 - (100 / (1 + (gain / loss)))
            
            df['LL_14'] = df['low'].rolling(14).min()
            df['HH_14'] = df['high'].rolling(14).max()
            df['%K'] = 100 * (df['close'] - df['LL_14']) / (df['HH_14'] - df['LL_14'] + 1e-10)

            # OBV, MFI
            df['OBV'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
            df['OBV_EMA20'] = df['OBV'].ewm(span=20, adjust=False).mean()
            
            df['TP'] = (df['high'] + df['low'] + df['close']) / 3
            df['RMF'] = df['TP'] * df['volume']
            df['Prev_TP'] = df['TP'].shift(1)
            df['PMF'] = np.where(df['TP'] > df['Prev_TP'], df['RMF'], 0)
            df['NMF'] = np.where(df['TP'] < df['Prev_TP'], df['RMF'], 0)
            df['MFI_14'] = 100 - (100 / (1 + df['PMF'].rolling(14).sum() / (df['NMF'].rolling(14).sum() + 1e-10)))

            # BOLLINGER & ATR
            df['STD_20'] = df['close'].rolling(window=20).std()
            df['BB_Upper'] = df['SMA_20'] + (df['STD_20'] * 2)
            df['BB_Lower'] = df['SMA_20'] - (df['STD_20'] * 2)
            df['Bandwidth'] = (df['BB_Upper'] - df['BB_Lower']) / df['SMA_20'] * 100
            df['ATR_14'] = df['TR'].rolling(window=14).mean()

            # PIVOT POINTS
            df['Pivot'] = (df['Prev_H'] + df['Prev_L'] + df['Prev_C']) / 3
            df['R1'] = (2 * df['Pivot']) - df['Prev_L']
            df['S1'] = (2 * df['Pivot']) - df['Prev_H']
            df['R2'] = (df['Pivot']) + (df['Prev_H'] - df['Prev_L'])
            df['S2'] = (df['Pivot']) - (df['Prev_H'] - df['Prev_L'])
            
            df = df.dropna()
            if df.empty: return
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            price = last['close'] * 1000
            
            # ==========================================
            # 2. REGIME DETECTION ENGINE (ĐỌC BỐI CẢNH)
            # ==========================================
            adx_val = last['ADX_14']
            
            # Điều kiện tăng xu hướng
            is_uptrend = last['close'] > last['EMA_50'] and last['EMA_50'] > last['EMA_200'] and adx_val > 20
            # Điều kiện giảm xu hướng
            is_downtrend = last['close'] < last['EMA_50'] and last['EMA_50'] < last['EMA_200'] and adx_val > 20
            # Sideway (Thị trường lững lờ)
            is_sideway = adx_val < 20
            
            if is_uptrend:
                regime_label = "🟢 Cổ phiếu đang có Sóng Trưởng (Sức tăng khỏe & Bền vững)"
                regime_advice = """
                **Ý nghĩa thực tế:** Cổ phiếu này đang vượt mọi rào cản, xu hướng đi lên rất vững chắc (đã đè nằm lên 50 ngày và 200 ngày trung bình). Lực đẩy cũng đang rất mạnh.
                \n👉 **Bạn nên làm gì:** Người mới hay có tâm lý Cổ Lên Cao Chóng Mặt thì đem Bán (hoặc Sợ Không Dám Mua). Nhưng theo thuật toán, **BẠN KHÔNG NÊN ĐOÁN ĐỈNH** lúc này. 
                Cách tốt nhất là CHỜ NHŨNG NHỊP GIẢM NHẸ (Kéo lùi/Pullback) để lên tàu, vì một xe tải đang lên đà không thể dừng ngay được!
                """
            elif is_downtrend:
                regime_label = "🔴 Cổ phiếu đang Rơi Tự Do (Nằm dưới đường sinh tử)"
                regime_advice = """
                **Ý nghĩa thực tế:** Cổ phiếu này đang thủng đáy dài hạn (Đường trung bình 200 ngày báo động đỏ). Bất cứ ai cầm cổ phiếu này từ nửa năm trước đến nay đều đang Lỗ, do vậy mọi đợt tăng nhích xíu lẻ tẻ đều sẽ bị họ 'Xả' hàng bán thoát mạng.
                \n👉 **Bạn nên làm gì:** **CẤM MUA! CẤM BẮT ĐÁY!** Những người mới phân tích kỹ thuật hay nhìn thấy giá Lún sâu lại tưởng là Rẻ, nhưng rẻ rồi vẫn có thể còn rớt đáy vực. Trừ khi có dấu hiệu Dòng tiền cực khủng phá vỡ, nếu không thì đứng ngoài.
                """
            else:
                regime_label = "⚖️ Cổ phiếu đang Đi Ngang (Sideway/Tích Luỹ/Giằng Co)"
                regime_advice = """
                **Ý nghĩa thực tế:** Biểu đồ cổ phiếu đang dao động chán nản trong một cái biên lồng hẹp. Ở đây không có đội nào đang gom thật mạnh, cũng chẳng ai bán tháo. Trạng thái vô trùng.
                \n👉 **Bạn nên làm gì:** Đây là thị trường chơi 'Pinball'. Bật xuống hố quá sâu (quá bán) thì bật nẩy lên; bay vọt lên cao tí là bị tát ngược xuống. Nếu mua, nên chốt lời ngắn hạn ăn phần trăm ít; không ôm mộng X2 tài khoản ở giai đoạn này.
                """

            ta_reasons = []
            score = 0
            
            # 1. Volume Confirmation
            if last['OBV'] > last['OBV_EMA20']:
                score += 1
                ta_reasons.append("🐳 **Soi Dòng Tiền Lớn (Vết Chân Cá Mập):** Tôi thấy Dòng tiền Thực (OBV) đang lớn hơn Khối lượng trung bình dạo gần đây. Tức là các Lệnh mua To và Quyết Liệt đang bơm vào nhặt cổ phiếu lẳng lặng. Rất Tích Cực!")
            else:
                score -= 1
                ta_reasons.append("⚠️ **Cẩn Khúc Gãy Dòng Tiền:** Tiền trên thị trường đang rút ra lẻ tẻ (hoặc không ai chịu bỏ vốn vô). Nếu Giá tăng mà không thấy ai giao dịch, hãy CẨN THẬN đây là Mức Giá Ảo (Bẫy Giá Lên).")
                
            # 2. Momentum Logic based on Regime
            if is_sideway:
                if last['RSI_14'] < 30 or last['%K'] < 20:
                    score += 2
                    ta_reasons.append("🎯 **Cơ Hội Chớp Nhoáng (Over-sold):** Cổ phiếu này vừa bị BÁN THÁO quá đà một cách mù quáng (RSI rớt thảm). Do đang Sideway, đây là vùng an toàn để bạn Gom nhặt giá bèo, chờ nó hồi lại.")
                elif last['RSI_14'] > 70 or last['%K'] > 80:
                    score -= 2
                    ta_reasons.append("🔥 **Hãy Kiềm Chế Hưng Phấn (Over-bought):** Trên các hội nhóm lúc này chắc chắn lùng bùng hô hào Giá sẽ bay. Kệ họ, đây là lúc Giá quá ảo so với thực tế ngắn hạn. Nếu bạn Mua theo lúc này, 90% bạn sẽ Đua ở Mức Đỉnh ngắn.")
            elif is_uptrend:
                if last['close'] > prev['high'] and last['MACD'] > last['Signal']:
                    score += 2
                    ta_reasons.append("🚀 **Vượt Ngục Thành Công (Breakout):** Cổ phiếu này chính thức phá đỉnh cũ để đi tìm bầu trời mới. Kèm đà đang cực khoẻ, bạn hoàn toàn có thể mua Mở Rộng vị thế theo sóng.")
                if last['close'] <= last['EMA_50'] * 1.02 and last['close'] >= last['EMA_50'] * 0.98:
                    score += 3
                    ta_reasons.append("♻️ **Điểm Mua Vàng (Pullback Thần Thánh):** Nó vừa rớt giảm chút do nhà đầu tư non tay chốt lời, rớt ngay chạm Cản Hỗ Trợ Dày (EMA 50 ngày). Đây là CƠ HỘI HIẾM có để Mua vé lên một con Tàu nhanh với độ Rủi ro thấp nhất có thể.")
                    
            # 3. Volatility Evaluation (Bollinger)
            is_squeeze = last['Bandwidth'] < df['Bandwidth'].quantile(0.15)
            if is_squeeze:
                ta_reasons.append("🧨 **Thắt Cổ Chai Áp Lực (Bollinger Squeeze):** Đây là lúc biểu đồ nén lò xo chặt cực nén. Lịch sử đã chứng minh, nén càng chặt, ngày mai hoặc thứ 2 tuần sau Rất Dễ Xảy Ra Đại Bứt Phá (Hoặc Tăng rực, Hoặc Rơi thẳm)! Quan sát kỹ.")
                if is_uptrend: score += 1

            # ==========================================
            # 3. MULTI-TIMEFRAME FORECAST ENGINE
            # (Dự Báo Đa Khung – Cơ Sở Để Ra Quyết Định CW)
            # ==========================================
            
            # EMA ngắn hạn
            df['EMA_7'] = df['close'].ewm(span=7, adjust=False).mean()
            df['EMA_14'] = df['close'].ewm(span=14, adjust=False).mean()
            df['EMA_21'] = df['close'].ewm(span=21, adjust=False).mean()
            
            # RSI 7 ngày (siêu nhạy ngắn hạn)
            delta7 = df['close'].diff()
            gain7 = (delta7.where(delta7 > 0, 0)).ewm(alpha=1/7, adjust=False).mean()
            loss7 = (-delta7.where(delta7 < 0, 0)).ewm(alpha=1/7, adjust=False).mean()
            df['RSI_7'] = 100 - (100 / (1 + (gain7 / loss7)))
            df = df.dropna()
            last = df.iloc[-1]
            prev = df.iloc[-2]
            price = last['close'] * 1000
            atr = last['ATR_14'] * 1000
            
            def compute_bull_score(df_ref, ema_col, rsi_col='RSI_14'):
                """Tính điểm xác suất tăng (0-100) dựa trên 5 lớp chỉ báo."""
                r = df_ref.iloc[-1]
                p = df_ref.iloc[-2]
                pts = 0
                # Lớp 1: Trend (EMA)
                if r['close'] > r.get(ema_col, r['close']): pts += 20
                # Lớp 2: Trend Strength (ADX)
                if r.get('ADX_14', 0) > 20: pts += 20
                # Lớp 3: Momentum (RSI chưa quá mua)
                rsi_val = r.get(rsi_col, r.get('RSI_14', 50))
                if 30 < rsi_val < 70: pts += 20
                elif rsi_val <= 30: pts += 25  # Oversold = cơ hội tốt
                # Lớp 4: Momentum (MACD Hist đang tăng)
                r_hist = r.get('Hist', 0)
                p_hist = p.get('Hist', 0)
                if r_hist > p_hist: pts += 20
                # Lớp 5: Volume/Dòng tiền (OBV > EMA20)
                if r.get('OBV', 0) > r.get('OBV_EMA20', 0): pts += 20
                return min(pts, 100)

            # Tính điểm từng khung
            score_7  = compute_bull_score(df, 'EMA_7',  'RSI_7')
            score_14 = compute_bull_score(df, 'EMA_14', 'RSI_14')
            score_21 = compute_bull_score(df, 'EMA_21', 'RSI_14')
            score_30 = compute_bull_score(df, 'EMA_50', 'RSI_14')
            
            def forecast_band(px, atr_val, factor, bull_s):
                """Tính vùng giá dự báo có trọng số theo hướng xu hướng."""
                bias = (bull_s - 50) / 50  # -1 → +1
                center = px + (atr_val * factor * bias)
                lo = center - atr_val * factor
                hi = center + atr_val * factor
                return max(lo, 0), hi

            b7_lo,  b7_hi  = forecast_band(price, atr, 1.5, score_7)
            b14_lo, b14_hi = forecast_band(price, atr, 2.2, score_14)
            b21_lo, b21_hi = forecast_band(price, atr, 3.0, score_21)
            b30_lo, b30_hi = forecast_band(price, atr, 4.0, score_30)

            def signal_from_score(s):
                if s >= 64:   return "🟢", "CALL", "#00C48C"
                elif s >= 50: return "🟡", "THEO DÕI", "#F0A500"
                elif s >= 40: return "⚖️", "KHÔNG RÕ", "#888"
                else:         return "🔴", "PUT / TRÁNH", "#FF5252"

            ico7,  lbl7,  clr7  = signal_from_score(score_7)
            ico14, lbl14, clr14 = signal_from_score(score_14)
            ico21, lbl21, clr21 = signal_from_score(score_21)
            ico30, lbl30, clr30 = signal_from_score(score_30)

            # ==========================================
            # 4. PRESENTATION LAYER
            # ==========================================
            st.markdown(f"### 🛡️ Trạng Thái Tổng Cục: **{regime_label}**")
            st.info(f"{regime_advice}")

            # ─────────────── PANEL DỰ BÁO ĐA KHUNG ───────────────
            st.markdown("---")
            st.subheader("📡 Dự Báo Xu Hướng Đa Khung – Cơ Sở Ra Quyết Định Chứng Quyền")
            st.caption("Xác suất tăng (Bull Score) được tính từ 5 lớp chỉ báo: Xu Hướng · ADX · RSI · MACD · Dòng Tiền OBV. Dùng để quyết định nên mua CALL hay PUT cho chứng quyền tương ứng.")

            st.markdown(f"""
<style>
.forecast-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 12px 0 24px 0;
}}
.fc-card {{
    background: rgba(255,255,255,0.04);
    border-radius: 14px;
    padding: 18px 20px 16px;
    border: 1px solid rgba(255,255,255,0.08);
    position: relative;
    overflow: hidden;
}}
.fc-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--fc-clr);
}}
.fc-horizon {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 10px;
}}
.fc-signal {{
    font-size: 22px;
    font-weight: 800;
    color: var(--fc-clr);
    margin-bottom: 4px;
}}
.fc-score {{
    font-size: 13px;
    color: #ccc;
    margin-bottom: 12px;
}}
.fc-score span {{
    font-weight: 700;
    color: var(--fc-clr);
    font-size: 16px;
}}
.fc-bar-wrap {{
    background: rgba(255,255,255,0.07);
    border-radius: 20px;
    height: 6px;
    margin-bottom: 12px;
    overflow: hidden;
}}
.fc-bar {{
    height: 6px;
    border-radius: 20px;
    background: var(--fc-clr);
}}
.fc-band {{
    font-size: 12px;
    color: #aaa;
    border-top: 1px solid rgba(255,255,255,0.07);
    padding-top: 10px;
    line-height: 1.7;
}}
.fc-band strong {{
    color: #eee;
}}
.fc-warrant-tip {{
    margin-top: 8px;
    font-size: 11px;
    padding: 6px 10px;
    border-radius: 8px;
    background: rgba(255,255,255,0.06);
    color: #bbb;
}}
</style>

<div class="forecast-grid">

  <div class="fc-card" style="--fc-clr:{clr7}">
    <div class="fc-horizon">⏱ 7 NGÀY TỚI</div>
    <div class="fc-signal">{ico7} {lbl7}</div>
    <div class="fc-score">Xác suất tăng: <span>{score_7}%</span></div>
    <div class="fc-bar-wrap"><div class="fc-bar" style="width:{score_7}%"></div></div>
    <div class="fc-band">
      Vùng giá kỳ vọng:<br>
      <strong>{b7_lo:,.0f} ₫ – {b7_hi:,.0f} ₫</strong>
    </div>
    <div class="fc-warrant-tip">💡 CW đáo hạn &lt;10 ngày: Dùng khung này quyết định vào/thoát.</div>
  </div>

  <div class="fc-card" style="--fc-clr:{clr14}">
    <div class="fc-horizon">⏱ 14 NGÀY TỚI</div>
    <div class="fc-signal">{ico14} {lbl14}</div>
    <div class="fc-score">Xác suất tăng: <span>{score_14}%</span></div>
    <div class="fc-bar-wrap"><div class="fc-bar" style="width:{score_14}%"></div></div>
    <div class="fc-band">
      Vùng giá kỳ vọng:<br>
      <strong>{b14_lo:,.0f} ₫ – {b14_hi:,.0f} ₫</strong>
    </div>
    <div class="fc-warrant-tip">💡 CW đáo hạn 10–20 ngày: Khung chủ lực để ra quyết định.</div>
  </div>

  <div class="fc-card" style="--fc-clr:{clr21}">
    <div class="fc-horizon">⏱ 21 NGÀY TỚI</div>
    <div class="fc-signal">{ico21} {lbl21}</div>
    <div class="fc-score">Xác suất tăng: <span>{score_21}%</span></div>
    <div class="fc-bar-wrap"><div class="fc-bar" style="width:{score_21}%"></div></div>
    <div class="fc-band">
      Vùng giá kỳ vọng:<br>
      <strong>{b21_lo:,.0f} ₫ – {b21_hi:,.0f} ₫</strong>
    </div>
    <div class="fc-warrant-tip">💡 CW đáo hạn 20–30 ngày: Xác nhận xu hướng trung hạn.</div>
  </div>

  <div class="fc-card" style="--fc-clr:{clr30}">
    <div class="fc-horizon">⏱ 30 NGÀY TỚI</div>
    <div class="fc-signal">{ico30} {lbl30}</div>
    <div class="fc-score">Xác suất tăng: <span>{score_30}%</span></div>
    <div class="fc-bar-wrap"><div class="fc-bar" style="width:{score_30}%"></div></div>
    <div class="fc-band">
      Vùng giá kỳ vọng:<br>
      <strong>{b30_lo:,.0f} ₫ – {b30_hi:,.0f} ₫</strong>
    </div>
    <div class="fc-warrant-tip">💡 CW đáo hạn 30–45 ngày: Dùng để lọc entry, không vào khi tín hiệu trái chiều.</div>
  </div>

</div>

<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:14px 18px;margin-bottom:16px;font-size:13px;color:#bbb;line-height:1.8">
  <strong style="color:#eee">📖 Cách Đọc Bảng Này:</strong><br>
  • <strong style="color:#00C48C">🟢 CALL ≥ 64%</strong>: Dòng tiền và xu hướng đang hậu thuẫn chiều TĂNG → Ưu tiên mua CW Call.<br>
  • <strong style="color:#F0A500">🟡 THEO DÕI 50-63%</strong>: Tín hiệu dương nhẹ nhưng chưa thuyết phục → Chờ xác nhận thêm.<br>
  • <strong style="color:#888">⚖️ KHÔNG RÕ 40-49%</strong>: Thị trường giằng co, không vào lệnh ở khung này.<br>
  • <strong style="color:#FF5252">🔴 PUT &lt; 40%</strong>: Áp lực giảm chiếm ưu thế → Tránh CW Call, cân nhắc CW Put nếu có.<br>
  <br>
  <strong style="color:#eee">⚠️ Lưu ý:</strong> Vùng giá kỳ vọng được tính dựa trên ATR (biên độ dao động thực) × hệ số thời gian. 
  Đây là vùng xác suất thống kê, <em>không phải cam kết chính xác</em>. Dùng để chọn CW có Strike Price nằm trong vùng này.
</div>
""", unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader(f"📊 Báo Cáo Sức Khỏe Lõi Cho: {sym}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "Đóng Cửa Cuối Cùng", 
                f"{price:,.0f} đ", 
                f"{((last['close']-prev['close'])/prev['close']*100):.2f}%", 
                help="Đây là giá kết thúc cuối ngày giao dịch vừa rồi, quy ra VNĐ."
            )
            
            trend_str = f"Lực {adx_val:.1f}/100"
            c2.metric(
                "Độ Khoẻ Sóng Tăng Giảm (ADX)", 
                trend_str, 
                "Sóng Khoẻ (Áp Đảo)" if adx_val > 20 else "Sóng Yếu (Nhạt nhoà)", 
                delta_color="normal" if adx_val > 20 else "off",
                help="ADX là nhiệt kế đo mức độ 'cuồng' của chứng khoán. Trị số lớn hơn 20 chứng tỏ nó đang đi rất lỳ (rất khó đảo chiều)."
            )
            
            obv_trend = "Cá Mập Vào Gom" if last['OBV'] > last['OBV_EMA20'] else "Cá Mập Đang Thoát"
            c3.metric(
                "Nhận Diện Dòng Tiền Quy Mô Lớn (OBV/MFI)", 
                "Tích Cực" if last['OBV'] > last['OBV_EMA20'] else "Tiêu Cực", 
                obv_trend, 
                delta_color="normal" if "Gom" in obv_trend else "inverse",
                help="Kết hợp giữa Giá và Khối Lượng Tiền. Nếu Giá Giảm nhưng chữ này báo 'Gom', chứng tỏ Đội tay to đang đè lén lút giá rẻ để nhặt hàng."
            )
            
            atr = last['ATR_14'] * 1000
            c4.metric(
                "Biên Độ Biến Động Trung Bình (ATR)", 
                f"Lắc: {atr:,.0f} đ/ngày", 
                "Dùng Đo Ngưỡng Chịu Nhiệt", 
                delta_color="off",
                help="ATR cảnh báo trung bình 1 ngày cổ phiếu này nhảy cỡ nào. Khoảng 'Lắc' càng bự, chứng tỏ cổ phiếu rủi ro đau tim càng to."
            )
            
            st.markdown("---")
            st.markdown("### 👨‍💼 PHIÊN DỊCH DẤU TÍCH GIAO DỊCH TỪ BIỂU ĐỒ NẾN")
            with st.container(border=True):
                st.markdown("#### Tại sao Thuật toán lại chấm điểm như vậy?")
                for r in ta_reasons:
                    st.markdown(r)
                
                st.markdown("---")
                if is_downtrend:
                    st.error("☠️ **HƯỚNG DẪN CUỐI SAU LỌC: ĐỨNG NGOÀI (CẤM MUA)**\n\nNơi này sinh ra không phải để kiếm tiền. Không được mua dò đáy.")
                elif score >= 3: 
                    st.success("💎 **HƯỚNG DẪN CUỐI SAU LỌC: CƠ HỘI (MUA QUANH VÙNG NÀY)**\n\nXu hướng tốt, Cấu trúc Dòng tiền hoàn hảo, Xác suất Lới Lãi đè bẹp Rủi RO Mất Tiền. BẠN CÓ THỂ RẢI VỐN VÀO.")
                elif score >= 1: 
                    st.info("⚖️ **HƯỚNG DẪN CUỐI SAU LỌC: THĂM DÒ DÈ ĐẶT**\n\nMẫu hình chưa Thuyết Phục trăm phần trăm, có thể ném đã thử tỉ trọng bé xíu để lấy vị thế chờ thời.")
                else: 
                    st.warning("⚠️ **HƯỚNG DẪN CUỐI SAU LỌC: BỎ TAY KHỎI BÀN PHÍM (ĐỨNG NGOÀI)**\n\nKhông nằm trong điểm Buy Setups đẹp, thà cầm tiền mặt đi uống cafe còn sướng hơn cố múc lúc này.")

            # Trả lời 4 Câu hỏi cốt lõi The Professional
            sl_price = price - (1.5 * atr) if not is_downtrend else price + (1.5 * atr)
            
            regime_icon = "🟢" if is_uptrend else "🔴" if is_downtrend else "⚖️"
            regime_text = "Tấn Công – Theo Sóng Tăng" if is_uptrend else "Phòng Thủ – Cầm Tiền Canh Chừng" if is_downtrend else "Trung Lập – Bắt Ngắn Kiếm Ăn"
            regime_color = "#00C48C" if is_uptrend else "#FF4B4B" if is_downtrend else "#F0A500"
            
            st.markdown("---")
            st.subheader("🗺️ Bản Đồ Hành Động – 4 Câu Người Pro Tự Hỏi Trước Mỗi Lệnh")
            st.caption("Đừng hỏi 'ngày mai tăng hay giảm?'. Người chuyên nghiệp chỉ hỏi 4 câu sau:")

            st.markdown(f"""
<style>
.trade-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 16px;
}}
.trade-card {{
    background: rgba(255,255,255,0.04);
    border-radius: 14px;
    padding: 22px 26px;
    border: 1px solid rgba(255,255,255,0.09);
}}
.trade-card .step-badge {{
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 6px;
}}
.trade-card .card-title {{
    font-size: 15px;
    font-weight: 600;
    color: #eee;
    margin-bottom: 14px;
    line-height: 1.4;
}}
.trade-card .card-value {{
    font-size: 26px;
    font-weight: 800;
    margin-bottom: 10px;
    font-family: 'Courier New', monospace;
}}
.trade-card .card-tip {{
    font-size: 13px;
    color: #aaa;
    line-height: 1.55;
    border-top: 1px solid rgba(255,255,255,0.07);
    padding-top: 10px;
    margin-top: 4px;
}}
.accent-green {{ color: {regime_color}; }}
.accent-red {{ color: #FF5252; }}
.accent-orange {{ color: #FFB74D; }}
.accent-teal {{ color: #4DD0E1; }}
</style>

<div class="trade-grid">

  <div class="trade-card">
    <div class="step-badge">Bước 1 — Nhận Diện Chiến Trường</div>
    <div class="card-title">Thị trường đang ở thế nào? Tôi nên Tấn Công hay Phòng Thủ?</div>
    <div class="card-value accent-green">{regime_icon} {regime_text}</div>
    <div class="card-tip">
        {'Cấu trúc giá đang ngự trên tất cả đường trung bình dài hạn (EMA 50 & 200). Đây là bối cảnh thuận lợi nhất để bỏ vốn – <strong>ưu tiên mua những nhịp kéo lùi nhẹ, không đuổi giá</strong>.' if is_uptrend else 
         'Cổ phiếu đang lủng dưới đường sinh tử EMA 200. Bất kỳ lần tăng nào cũng là cơ hội để người kẹt hàng tháo chạy. <strong>Không bắt đáy, không dò mua.</strong>' if is_downtrend else 
         'Thị trường không thuộc về bên nào. Cung cầu đang giằng co ngang biên. <strong>Nếu có vào, chỉ ăn ngắn và chốt sớm.</strong>'}
    </div>
  </div>

  <div class="trade-card">
    <div class="step-badge">Bước 2 — Điểm Vào Lệnh</div>
    <div class="card-title">Mức giá nào là "Mua Sale Off" an toàn nhất?</div>
    <div class="card-value accent-teal">{(last['Pivot']*1000):,.0f} ₫</div>
    <div class="card-tip">
        Đây là <strong>vùng Pivot Support</strong> – mức giá được cộng đồng trader kỹ thuật dùng làm điểm neo. 
        Khi giá kéo về vùng này mà <em>không thủng</em>, cú bật lên thường rất mạnh vì nhiều lệnh mua cùng xuất hiện hỗ trợ một lúc.
        👉 <em>Không mua giá đang trần xanh. Hãy đặt lệnh treo ở mức này và chờ.</em>
    </div>
  </div>

  <div class="trade-card">
    <div class="step-badge">Bước 3 — Cắt Lỗ Kỷ Luật</div>
    <div class="card-title">Nếu kế hoạch sai, tôi cắt lệnh ở đâu?</div>
    <div class="card-value accent-red">{sl_price:,.0f} ₫</div>
    <div class="card-tip">
        Hệ thống tính mức này dựa trên <strong>ATR × 1.5</strong> – tức là biên độ dao động thực trung bình của cổ phiếu nhân 1.5 lần.
        Nếu giá xuyên thủng mốc này, <strong>bán ngay không chần chừ</strong>. Đây không còn là "kéo lùi bình thường" mà là tín hiệu cấu trúc giá đã vỡ.
        ⚠️ <em>Đặt cắt lỗ trước khi vào lệnh, không phải sau khi đã lỗ.</em>
    </div>
  </div>

  <div class="trade-card">
    <div class="step-badge">Bước 4 — Chốt Lời Từng Phần</div>
    <div class="card-title">Khi đang thắng, chốt lời ở đâu?</div>
    <div class="card-value accent-orange">R1: {(last['R1']*1000):,.0f} ₫ → R2: {(last['R2']*1000):,.0f} ₫</div>
    <div class="card-tip">
        <strong>R1 (Kháng Cự Thứ Nhất):</strong> Bán 50% khi chạm đây – lấy lãi, giữ nửa còn lại.<br>
        <strong>R2 (Kháng Cự Đỉnh):</strong> Đóng toàn bộ vị thế khi chạm đây.<br>
        💡 <em>Bí quyết: Không bán hết ở R1, để một phần "cưỡi sóng" lên R2, tối đa hóa lợi nhuận mà không tham quá mức.</em>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)
                
            st.markdown("---")
            # Draw charts
            tab1, tab2, tab3 = st.tabs(["Hậu Trường Thuật Toán A: Chỉ Báo Mức Gián Cản", "Hậu Trường Thuật Toán B: Cơn Khát & Đo Sóng", "Hậu Trường Thuật Toán C: Khối Lượng Tiền Ẩn"])
            with tab1:
                st.markdown("**1. Đường đi của Giá so với Sinh Tử Môn (EMA 50 & 200 ngày):**")
                chart_df = df[['close', 'EMA_50', 'EMA_200']].tail(90)
                st.line_chart(chart_df, color=["#00F0FF", "#FFA500", "#FF4B4B"])
                st.caption("Nếu Đường Xanh Băng Băng bay xa ở phía trên Cùng, đó là mỏ vàng uptrend.")
            with tab2:
                c_ta_1, c_ta_2 = st.columns(2)
                with c_ta_1:
                    st.markdown("**2. RSI (Nhiệt kế Chán Nản Chứ Không Phải Sức Mạnh):**")
                    st.line_chart(df['RSI_14'].tail(90), color="#FF00FF")
                    st.caption("Ngóc Trên 70 là sắp bị Giội nước lạnh, Chìm Nhịp 30 là điểm Nẩy Sóng Hồi.")
                with c_ta_2:
                    st.markdown("**3. ADX (Tần Số Cứng Đầu):**")
                    st.line_chart(df['ADX_14'].tail(90), color="#00FF00")
                    st.caption("Số càng bự, xu hướng càng Bền Chặt, Ít lật lọng tráo trở.")
            with tab3:
                st.markdown("**4. Dòng Dịch Chuyển Trí Tuệ (MFI - MFI Đong Lực Mua Tiền Thay Vì Đếm Xác Cổ):**")
                st.line_chart(df['MFI_14'].tail(90), color="#F0E68C")
                st.caption("Tăng vọt cho thấy Nhóm Tay Nhập Hàng Chôn Vốn.")
