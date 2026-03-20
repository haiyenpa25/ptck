def calculate_spread_factor(bid: float, ask: float) -> float:
    """Calculates spread percentage. Returns 0 on spread errors/zeros."""
    if bid <= 0:
        return 0.0
    return round((ask - bid) / bid * 100, 2)

def calculate_time_factor(days_to_expiration: int) -> str:
    """Returns the DTE risk categorization based on remaining days."""
    if days_to_expiration < 15:
        return "HIGH_RISK"
    elif days_to_expiration <= 20:
        return "MEDIUM_RISK"
    else:
        return "SAFE"

def compute_c_score(spread: float, time_f: str, base_momentum_pct: float, delta: float = 1.0, gearing: float = 1.0) -> dict:
    """
    Computes a quantitative C-Score (0-100) and returns the breakdown.
    Returns: {
        'total': float,
        'spread_score': float,
        'time_score': float,
        'mome_score': float,
        'cw_mome': float
    }
    """
    score = 50.0  # Base neutral score
    
    # 1. Spread Scoring (Tighter spreads = safer)
    s_score = 0.0
    if spread <= 1.0:
        s_score = 20.0
    elif spread <= 3.0:
        s_score = 10.0
    elif spread > 5.0:
        s_score = -10.0
    score += s_score
        
    # 2. Time Factor Risk
    t_score = 0.0
    if time_f == "SAFE":
        t_score = 15.0
    elif time_f == "HIGH_RISK":
        t_score = -20.0
    score += t_score
        
    # 3. Delta-Adjusted Derived Momentum 
    m_score = 0.0
    cw_momentum_pct = base_momentum_pct * delta * gearing
    if cw_momentum_pct > 2.0:
        m_score = 25.0
    elif cw_momentum_pct > 0.5:
        m_score = 10.0
    elif cw_momentum_pct < -0.5:
        m_score = -15.0
    elif cw_momentum_pct < -2.0:
        m_score = -30.0
    score += m_score
        
    final_score = min(100.0, max(0.0, score))
    return {
        'total': final_score,
        'spread_score': s_score,
        'time_score': t_score,
        'mome_score': m_score,
        'cw_mome': cw_momentum_pct
    }
