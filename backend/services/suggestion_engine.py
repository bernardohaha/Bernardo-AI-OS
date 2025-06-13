import numpy as np
import talib
from backend.services.binance_service import get_candles, get_current_price
from backend.services.market_analysis_service import analyze_orderbook_pressure
from backend.services.zone_analysis_service import (
    detect_price_zones,
    calculate_fibonacci_zones,
)


def analyze_symbol(symbol, interval="1h"):
    closes = get_candles(symbol, interval=interval)
    prices = np.array(closes)

    if len(prices) < 30:
        return {"symbol": symbol, "error": "Not enough data", "interval": interval}

    price_now = get_current_price(symbol) or prices[-1]

    rsi = talib.RSI(prices, timeperiod=14)[-1]
    ema_fast = talib.EMA(prices, timeperiod=9)[-1]
    ema_slow = talib.EMA(prices, timeperiod=21)[-1]
    macd, macdsignal, _ = talib.MACD(
        prices, fastperiod=12, slowperiod=26, signalperiod=9
    )
    macd_signal = macd[-1] - macdsignal[-1]

    kde_zones = detect_price_zones(closes[-50:], num_zones=2, bandwidth=0.01)
    fib_zones = calculate_fibonacci_zones(closes)

    combined_zones = kde_zones + fib_zones
    combined_zones = sorted(
        combined_zones, key=lambda z: abs(price_now - ((z[0] + z[1]) / 2))
    )

    support_zone = combined_zones[0] if combined_zones else (None, None)
    resistance_zone = combined_zones[-1] if combined_zones else (None, None)

    if (
        support_zone is not None
        and resistance_zone is not None
        and support_zone[0] is not None
        and resistance_zone[0] is not None
        and support_zone[0] > resistance_zone[0]
    ):
        support_zone, resistance_zone = resistance_zone, support_zone

    if support_zone[1] and resistance_zone[0] and support_zone[1] >= resistance_zone[0]:
        return {
            "symbol": symbol,
            "interval": interval,
            "price": round(price_now, 4),
            "recommendation": "HOLD",
            "orderbook_pressure": "N/A",
            "strength": "NEUTRAL",
            "confidence": 0.0,
            "expected_profit_pct": None,
            "buy_zone": {"min": None, "max": None},
            "sell_zone": {"min": None, "max": None},
        }

    in_buy_zone = (
        support_zone is not None
        and support_zone[0] is not None
        and support_zone[1] is not None
        and support_zone[0] <= price_now <= support_zone[1]
    )
    in_sell_zone = (
        resistance_zone is not None
        and resistance_zone[0] is not None
        and resistance_zone[1] is not None
        and resistance_zone[0] <= price_now <= resistance_zone[1]
    )

    recommendation = "HOLD"
    strength = "NEUTRAL"
    confidence = 0.0
    expected_profit = None

    points = 0
    total = 0
    if in_buy_zone:
        points += 1
    total += 1
    if rsi < 35:
        points += 1
    total += 1
    if ema_fast > ema_slow:
        points += 1
    total += 1
    if macd_signal > 0:
        points += 1
    total += 1

    if points >= 3:
        recommendation = "BUY"
        strength = "STRONG BUY"
        confidence = round(points / total, 2)
        expected_profit = (
            ((resistance_zone[1] - price_now) / price_now) * 100
            if resistance_zone[1]
            else None
        )
    else:
        points = 0
        total = 0
        if in_sell_zone:
            points += 1
        total += 1
        if rsi > 65:
            points += 1
        total += 1
        if ema_fast < ema_slow:
            points += 1
        total += 1
        if macd_signal < 0:
            points += 1
        total += 1

        if points >= 3:
            recommendation = "SELL"
            strength = "STRONG SELL"
            confidence = round(points / total, 2)
            expected_profit = (
                ((price_now - support_zone[0]) / support_zone[0]) * 100
                if support_zone[0]
                else None
            )

    if recommendation == "HOLD" and support_zone[0] and resistance_zone[1]:
        buy_avg = (support_zone[0] + support_zone[1]) / 2
        sell_avg = (resistance_zone[0] + resistance_zone[1]) / 2
        spread = sell_avg - buy_avg
        expected_profit = (spread / buy_avg) * 100
        distance = abs(price_now - buy_avg)
        confidence = max(0.0, 1 - (distance / spread)) if spread > 0 else 0.0

    if expected_profit is not None and expected_profit < 0:
        expected_profit = None
        confidence = 0.0
        recommendation = "HOLD"
        strength = "NEUTRAL"

    orderbook = analyze_orderbook_pressure(symbol)
    pressure = orderbook["pressure"] if orderbook and "pressure" in orderbook else "N/A"

    if recommendation.startswith("BUY") and pressure == "SELL_PRESSURE":
        recommendation = "HOLD (buy bloqueado por pressão de venda)"
        confidence *= 0.5
    elif recommendation.startswith("SELL") and pressure == "BUY_PRESSURE":
        recommendation = "HOLD (sell bloqueado por pressão de compra)"
        confidence *= 0.5

    print("DEBUG:")
    print("Preço atual:", price_now)
    print("RSI:", rsi)
    print("EMA9:", ema_fast)
    print("EMA21:", ema_slow)
    print("MACD:", macd_signal)
    print("Support zone:", support_zone)
    print("Resistance zone:", resistance_zone)

    return {
        "symbol": symbol,
        "interval": interval,
        "price": round(price_now, 4),
        "RSI": round(rsi, 2),
        "EMA9": round(ema_fast, 4),
        "EMA21": round(ema_slow, 4),
        "recommendation": recommendation,
        "orderbook_pressure": pressure,
        "strength": strength,
        "confidence": round(confidence, 2),
        "expected_profit_pct": round(expected_profit, 2)
        if expected_profit is not None
        else None,
        "buy_zone": {
            "min": round(support_zone[0], 4) if support_zone[0] else None,
            "max": round(support_zone[1], 4) if support_zone[1] else None,
        },
        "sell_zone": {
            "min": round(resistance_zone[0], 4) if resistance_zone[0] else None,
            "max": round(resistance_zone[1], 4) if resistance_zone[1] else None,
        },
    }
