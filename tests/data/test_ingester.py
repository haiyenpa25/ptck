from src.data.ingester import fetch_market_price
from unittest.mock import patch

@patch('src.data.ingester.stock_historical_data')
def test_fetch_market_price(mock_historical):
    import pandas as pd
    # Mocking vnstock3 response
    mock_historical.return_value = pd.DataFrame({
        'time': ['2026-03-19'], 'open': [100], 'high': [105], 'low': [99], 'close': [102], 'volume': [1000]
    })
    
    result = fetch_market_price('VNM')
    assert result['symbol'] == 'VNM'
    assert result['price'] == 102
