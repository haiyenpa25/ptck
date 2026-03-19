def evaluate_signals(c_score: float) -> str:
    """Evaluates C-Score to transition state machine."""
    if c_score < 50:
        return "IDLE"
    elif c_score <= 65:
        return "PROBE"
    elif c_score <= 80:
        return "CONFIRM"
    else:
        return "MAX_SIZE"
