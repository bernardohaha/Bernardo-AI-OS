import numpy as np


def calculate_rsi(closes: list[float], period: int = 14) -> list[float]:
    closes = np.array(closes, dtype=float)
    deltas = np.diff(closes)
    seed = deltas[:period]
    up = seed[seed > 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = [100 - 100 / (1 + rs)]
    for delta in deltas[period:]:
        gain = max(delta, 0)
        loss = -min(delta, 0)
        up = (up * (period - 1) + gain) / period
        down = (down * (period - 1) + loss) / period
        rs = up / down if down != 0 else 0
        rsi.append(100 - 100 / (1 + rs))
    return [None] * (period) + rsi


def calculate_ema(closes: list[float], period: int) -> list[float]:
    closes = np.array(closes, dtype=float)
    ema = [np.mean(closes[:period])]
    multiplier = 2 / (period + 1)
    for price in closes[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    return [None] * (period - 1) + ema


def calculate_macd(
    closes: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[list[float], list[float], list[float]]:
    fast_ema = calculate_ema(closes, fast_period)
    slow_ema = calculate_ema(closes, slow_period)
    macd_line = [f - s if f and s else None for f, s in zip(fast_ema, slow_ema)]
    macd_line_clean = [x for x in macd_line if x is not None]
    signal_line = calculate_ema(macd_line_clean, signal_period)
    signal_line_full = [None] * (len(macd_line) - len(signal_line)) + signal_line
    macd_hist = [
        m - s if m and s else None for m, s in zip(macd_line, signal_line_full)
    ]
    return macd_line, signal_line_full, macd_hist


def calculate_atr(
    highs: list[float], lows: list[float], closes: list[float], period: int
) -> float:
    tr = []
    for i in range(1, len(closes)):
        high = highs[i]
        low = lows[i]
        prev_close = closes[i - 1]
        tr_value = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr.append(tr_value)
    atr = np.mean(tr[-period:])
    return atr
