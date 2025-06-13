from backend.services.binance_service import get_candles
from backend.services.suggestion_engine import analyze_symbol
from backend.services.candlestick_patterns_service import detect_candlestick_patterns


def agent_macro(symbol):
    closes = get_candles(symbol, interval="1d", limit=300)
    if not closes or len(closes) < 30:
        return {"symbol": symbol, "error": "Not enough daily data"}

    result = analyze_symbol(symbol, interval="1h")
    result["agent"] = "macro"

    # Análise de padrões
    patterns = detect_candlestick_patterns(symbol, interval="1d", limit=50)
    if "error" not in patterns:
        result["pattern_implication"] = patterns["implication"]
        result["pattern_strength"] = patterns["strength"]
        result["detected_patterns"] = patterns["patterns"]  # lista com padrões

    return result
