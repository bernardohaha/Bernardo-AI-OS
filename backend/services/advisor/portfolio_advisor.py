import numpy as np
import talib
from services.binance_service import get_portfolio, get_candles
from services.logger_service import log_suggestion
from services import notifier_service  # <- Importa o notifier


def analyze_portfolio():
    portfolio = get_portfolio()
    symbols = [
        asset["symbol"] for asset in portfolio["assets"] if float(asset["total"]) > 0
    ]

    report = []

    for symbol in symbols:
        try:
            closes = get_candles(symbol)
            prices = np.array(closes)

            rsi = talib.RSI(prices, timeperiod=14)[-1]
            ema_fast = talib.EMA(prices, timeperiod=9)[-1]
            ema_slow = talib.EMA(prices, timeperiod=21)[-1]

            recent_high = np.max(prices[-20:])
            recent_low = np.min(prices[-20:])
            volume = np.sum(np.abs(np.diff(prices[-20:])))

            recommendation = "HOLD"
            if rsi < 30 and ema_fast > ema_slow:
                recommendation = "BUY"
            elif rsi > 70 and ema_fast < ema_slow:
                recommendation = "SELL"

            result = {
                "symbol": symbol,
                "RSI": round(rsi, 2),
                "EMA9": round(ema_fast, 4),
                "EMA21": round(ema_slow, 4),
                "recent_high": round(recent_high, 4),
                "recent_low": round(recent_low, 4),
                "volume": round(volume, 2),
                "recommendation": recommendation,
            }

            # Guarda o log da análise
            log_suggestion(result)
            report.append(result)

            # Aqui é onde fazemos o envio via Telegram
            if recommendation == "SELL":
                notifier_service.notify_sell(symbol, rsi)
            elif recommendation == "BUY":
                notifier_service.notify_buy(symbol, rsi)

        except Exception as e:
            report.append({"symbol": symbol, "error": str(e)})

    return report
