import numpy as np
import talib
from services.binance_service import get_candles


def analyze_swing(symbol):
    closes, highs, lows, volumes = get_candles(
        symbol, interval="4h", limit=200
    )  # Janela maior: 4h candles
    prices = np.array(closes)

    # RSI (Relative Strength Index)
    rsi = talib.RSI(prices, timeperiod=14)[-1]

    # EMA 50 e EMA 200 para tendência
    ema50 = talib.EMA(prices, timeperiod=50)[-1]
    ema200 = talib.EMA(prices, timeperiod=200)[-1]

    # Tendência geral
    trend = "Bullish" if ema50 > ema200 else "Bearish"

    # Breakout detection simples (últimos candles)
    recent_high = max(highs[-20:])  # último "topo" de 20 candles
    recent_low = min(lows[-20:])  # último "fundo" de 20 candles
    current_price = prices[-1]

    breakout_alert = None
    if current_price > recent_high * 1.01:  # 1% acima do topo recente
        breakout_alert = "Potential Breakout UP"
    elif current_price < recent_low * 0.99:  # 1% abaixo do fundo
        breakout_alert = "Potential Breakdown DOWN"

    return {
        "symbol": symbol,
        "RSI": round(rsi, 2),
        "EMA50": round(ema50, 4),
        "EMA200": round(ema200, 4),
        "trend": trend,
        "recent_high": recent_high,
        "recent_low": recent_low,
        "breakout_alert": breakout_alert,
    }
