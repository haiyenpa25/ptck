from src.engine.decision import evaluate_signals

def test_evaluate_signals():
    assert evaluate_signals(40.0) == "IDLE"
    assert evaluate_signals(55.0) == "PROBE"
    assert evaluate_signals(70.0) == "CONFIRM"
    assert evaluate_signals(85.0) == "MAX_SIZE"
