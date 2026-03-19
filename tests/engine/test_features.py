import pytest
from src.engine.features import calculate_spread_factor, calculate_time_factor

def test_calculate_spread_factor():
    # spread = (ask - bid) / bid * 100
    assert calculate_spread_factor(100.0, 102.0) == 2.0
    assert calculate_spread_factor(0.0, 10.0) == 0.0 # handle div by zero
    assert calculate_spread_factor(100.0, 100.0) == 0.0

def test_calculate_time_factor():
    """Test DTE (Days To Expiration) Risk"""
    assert calculate_time_factor(10) == "HIGH_RISK"
    assert calculate_time_factor(20) == "MEDIUM_RISK"
    assert calculate_time_factor(40) == "SAFE"
