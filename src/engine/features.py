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

def compute_c_score(spread: float, time_f: str, base_momentum_pct: float, delta: float = 1.0, gearing: float = 1.0) -> float:
    """Computes a quantitative C-Score (0-100) combining structural factors and REAL underlying momentum."""
    score = 50.0  # Base neutral score
    
    # 1. Spread Scoring (Tighter spreads = safer)
    if spread <= 1.0:
        score += 20
    elif spread <= 3.0:
        score += 10
    elif spread > 5.0:
        score -= 10
        
    # 2. Time Factor Risk
    if time_f == "SAFE":
        score += 15
    elif time_f == "HIGH_RISK":
        score -= 20
        
    # 3. Delta-Adjusted Derived Momentum 
    # Example: Base stock is up +2%, CW Delta 0.5, Gearing 4.0 -> CW momentum +4%
    cw_momentum_pct = base_momentum_pct * delta * gearing
    if cw_momentum_pct > 2.0:
        score += 25
    elif cw_momentum_pct > 0.5:
        score += 10
    elif cw_momentum_pct < -0.5:
        score -= 15
    elif cw_momentum_pct < -2.0:
        score -= 30
        
    return min(100.0, max(0.0, score))
