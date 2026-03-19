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
