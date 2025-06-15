from backend.services.ohlcv_stream_service import ohlcv_buffer


def get_ohlcv_data(symbol: str, interval: str = "1h", limit: int = 100):
    candles = list(ohlcv_buffer[symbol.upper()][interval])
    return candles[-limit:] if len(candles) >= limit else []
