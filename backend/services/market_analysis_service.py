from typing import Literal
import numpy as np
import talib

from backend.config.swing_config import SWING_CONFIG


def get_indicators(closes: list[float]) -> tuple[float, float, float]:
    closes = np.array(closes, dtype=float)

    rsi_period = SWING_CONFIG["rsi_period"]
    ema_fast_period = SWING_CONFIG["ema_fast_period"]
    ema_slow_period = SWING_CONFIG["ema_slow_period"]

    rsi = talib.RSI(closes, timeperiod=rsi_period)[-1]
    ema_fast = talib.EMA(closes, timeperiod=ema_fast_period)[-1]
    ema_slow = talib.EMA(closes, timeperiod=ema_slow_period)[-1]

    return rsi, ema_fast, ema_slow


def calculate_atr(highs: list[float], lows: list[float], closes: list[float]) -> float:
    highs = np.array(highs, dtype=float)
    lows = np.array(lows, dtype=float)
    closes = np.array(closes, dtype=float)

    atr_period = SWING_CONFIG["atr_period"]
    atr = talib.ATR(highs, lows, closes, timeperiod=atr_period)[-1]
    return atr


def get_macd_cross(closes: list[float]) -> Literal["bullish", "bearish", "neutral"]:
    closes = np.array(closes, dtype=float)

    fast = SWING_CONFIG["macd_fast_period"]
    slow = SWING_CONFIG["macd_slow_period"]
    signal = SWING_CONFIG["macd_signal_period"]
    threshold = SWING_CONFIG["macd_threshold"]

    macd, signal_line, hist = talib.MACD(
        closes, fastperiod=fast, slowperiod=slow, signalperiod=signal
    )

    diff = macd[-1] - signal_line[-1]
    if abs(diff) < threshold:
        return "neutral"
    return "bullish" if diff > 0 else "bearish"
