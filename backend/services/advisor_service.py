import numpy as np
import talib
from datetime import datetime
from backend.services.binance_service import (
    get_candles,
    get_portfolio,
    get_current_price,
)
from backend.services.market_analysis_service import analyze_orderbook_pressure
from services import order_service
from services import notifier_service
from backend.services.portfolio_service import (
    build_all_positions as get_portfolio_positions,
)


# Logs ainda em memória
advisor_logs = []


def analyze_symbol(symbol: str):
    candles = get_candles(symbol)
    prices = np.array(candles)
    closes = prices

    rsi = talib.RSI(closes, timeperiod=14)[-1]
    ema_fast = talib.EMA(closes, timeperiod=9)[-1]
    ema_slow = talib.EMA(closes, timeperiod=21)[-1]
    volume = np.random.randint(50000, 150000)  # Mock de volume

    recommendation = "HOLD"
    strength = "NEUTRAL"

    if rsi < 30 and ema_fast > ema_slow:
        recommendation = "BUY"
    elif rsi > 70 and ema_fast < ema_slow:
        recommendation = "SELL"

    # Análise de pressão do order book
    orderbook = analyze_orderbook_pressure(symbol)
    pressure = orderbook["pressure"] if orderbook and "pressure" in orderbook else "N/A"

    if recommendation == "BUY":
        if pressure == "SELL_PRESSURE":
            recommendation = "HOLD (buy bloqueado por pressão de venda)"
        elif pressure == "BUY_PRESSURE":
            strength = "STRONG BUY"
    elif recommendation == "SELL":
        if pressure == "BUY_PRESSURE":
            recommendation = "HOLD (sell bloqueado por pressão de compra)"
        elif pressure == "SELL_PRESSURE":
            strength = "STRONG SELL"

    log_entry = {
        "symbol": symbol,
        "price": closes[-1],
        "rsi": round(rsi, 2),
        "ema_fast": round(ema_fast, 4),
        "ema_slow": round(ema_slow, 4),
        "volume": volume,
        "recommendation": recommendation,
        "orderbook_pressure": pressure,
        "strength": strength,
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


def get_portfolio_analysis(portfolio_data):
    positions = get_portfolio_positions()
    enriched_data = []

    for item in portfolio_data:
        symbol_raw = item["symbol"]
        symbol = symbol_raw.replace("LD", "")
        if symbol in positions:
            entry_price = positions[symbol]["entry_price"]
            quantity = positions[symbol]["quantity"]

            price = get_current_price(symbol)
            if price is None:
                continue

            profit_usd = (price - entry_price) * quantity
            profit_percent = ((price - entry_price) / entry_price) * 100
            suggestion = suggest_action(
                profit_percent, symbol=symbol, entry_price=entry_price
            )

            enriched_data.append(
                {
                    "symbol": symbol,
                    "entry_price": entry_price,
                    "current_price": price,
                    "quantity": quantity,
                    "profit_usd": profit_usd,
                    "profit_percent": profit_percent,
                    "suggestion": suggestion,
                }
            )

    return enriched_data


def suggest_action(profit_percent, symbol=None, entry_price=None):
    if profit_percent >= 7:
        if symbol:
            notifier_service.notify_sell(symbol, profit_percent)
        return "Sugerir Venda"
    elif profit_percent <= -5:
        if symbol and entry_price:
            notifier_service.notify_buy(symbol, entry_price)
        return "Sugerir Comprar Mais"
    else:
        return "Manter"


def auto_generate_orders(portfolio_data):
    positions = get_portfolio_positions()
    existing_orders = order_service.get_orders()
    symbols_with_orders = [order["symbol"] for order in existing_orders]

    for item in portfolio_data:
        symbol_raw = item["symbol"]
        symbol = symbol_raw.replace("LD", "")

        if symbol in positions:
            entry_price = positions[symbol]["entry_price"]
            quantity = positions[symbol]["quantity"]
            price = get_current_price(symbol)
            if price is None:
                continue

            profit_usd = (price - entry_price) * quantity
            profit_percent = ((price - entry_price) / entry_price) * 100
            suggestion = suggest_action(profit_percent)

            if symbol + "USDT" not in symbols_with_orders:
                if suggestion == "Sugerir Venda":
                    order = {
                        "symbol": f"{symbol}USDT",
                        "type": "LIMIT",
                        "side": "SELL",
                        "price": round(price * 1.01, 2),
                        "quantity": quantity,
                        "status": "OPEN",
                    }
                    order_service.add_order(order)
                elif suggestion == "Sugerir Comprar Mais":
                    order = {
                        "symbol": f"{symbol}USDT",
                        "type": "LIMIT",
                        "side": "BUY",
                        "price": round(price * 0.99, 2),
                        "quantity": quantity * 0.5,
                        "status": "OPEN",
                    }
                    order_service.add_order(order)
