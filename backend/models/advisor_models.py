import numpy as np
import talib
from datetime import datetime
from backend.services.binance_service import get_candles, get_portfolio

# Para já vamos guardar os logs só em memória (mais tarde faremos persistência)
advisor_logs = []


def analyze_symbol(symbol: str):
    candles = get_candles(symbol)
    prices = np.array(candles)
    closes = prices

    rsi = talib.RSI(closes, timeperiod=14)[-1]
    ema_fast = talib.EMA(closes, timeperiod=9)[-1]
    ema_slow = talib.EMA(closes, timeperiod=21)[-1]
    volume = np.random.randint(50000, 150000)  # Mock de volume, depois ligamos à API

    recommendation = "HOLD"
    if rsi < 30 and ema_fast > ema_slow:
        recommendation = "BUY"
    elif rsi > 70 and ema_fast < ema_slow:
        recommendation = "SELL"

    log_entry = {
        "symbol": symbol,
        "price": closes[-1],
        "rsi": round(rsi, 2),
        "ema_fast": round(ema_fast, 4),
        "ema_slow": round(ema_slow, 4),
        "volume": volume,
        "recommendation": recommendation,
        "timestamp": datetime.utcnow().isoformat(),
    }

    advisor_logs.append(log_entry)
    return log_entry


def run_portfolio_analysis():
    portfolio = get_portfolio()
    for item in portfolio["balances"]:
        symbol = item["symbol"]
        analyze_symbol(symbol)


def get_advisor_logs():
    return advisor_logs
