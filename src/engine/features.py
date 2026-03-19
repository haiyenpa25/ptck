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

def compute_c_score(spread: float, time_f: str, momentum_pct: float) -> float:
    """Computes a quantitative C-Score (0-100) based on weighted factors."""
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
        
    # 3. Basic Momentum Proxy 
    if momentum_pct > 0:
        score += 15
    elif momentum_pct < -2:
        score -= 15
        
    return min(100.0, max(0.0, score))
