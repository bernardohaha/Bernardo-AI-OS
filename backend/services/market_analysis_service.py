import talib
import numpy as np
from backend.services.binance_service import get_candles
from backend.config import settings
from backend.services.binance_service import get_order_book


def analyze_symbol(symbol: str):
    closes = get_candles(symbol)
    prices = np.array(closes)

    rsi = talib.RSI(prices, timeperiod=settings.RSI_PERIOD)[-1]
    ema_fast = talib.EMA(prices, timeperiod=settings.EMA_FAST_PERIOD)[-1]
    ema_slow = talib.EMA(prices, timeperiod=settings.EMA_SLOW_PERIOD)[-1]
    recent_high = np.max(prices[-settings.RSI_PERIOD :])
    recent_low = np.min(prices[-settings.RSI_PERIOD :])
    volume = sum(closes[-settings.RSI_PERIOD :])

    recommendation = "HOLD"
    if rsi < 30 and ema_fast > ema_slow:
        recommendation = "BUY"
    elif rsi > 70 and ema_fast < ema_slow:
        recommendation = "SELL"

    breakout_alert = None
    if prices[-1] >= recent_high * (1 + settings.BREAKOUT_THRESHOLD):
        breakout_alert = "BREAKOUT_UP"
    elif prices[-1] <= recent_low * (1 - settings.BREAKOUT_THRESHOLD):
        breakout_alert = "BREAKOUT_DOWN"

    return {
        "symbol": symbol,
        "RSI": round(rsi, 2),
        "EMA_FAST": round(ema_fast, 4),
        "EMA_SLOW": round(ema_slow, 4),
        "recent_high": round(recent_high, 4),
        "recent_low": round(recent_low, 4),
        "volume": round(volume, 2),
        "recommendation": recommendation,
        "breakout_alert": breakout_alert,
    }


def analyze_orderbook_pressure(symbol: str, limit: int = 10):
    book = get_order_book(symbol, limit)
    if not book:
        return {"error": "Order book vazio ou falha na API"}

    total_bid_volume = sum([qty for _, qty in book["bids"]])
    total_ask_volume = sum([qty for _, qty in book["asks"]])
    spread = round(book["asks"][0][0] - book["bids"][0][0], 6)

    if total_bid_volume > total_ask_volume * 1.2:
        pressure = "BUY_PRESSURE"
    elif total_ask_volume > total_bid_volume * 1.2:
        pressure = "SELL_PRESSURE"
    else:
        pressure = "BALANCED"

    return {
        "symbol": symbol,
        "total_bid_volume": round(total_bid_volume, 2),
        "total_ask_volume": round(total_ask_volume, 2),
        "spread": spread,
        "pressure": pressure,
    }
