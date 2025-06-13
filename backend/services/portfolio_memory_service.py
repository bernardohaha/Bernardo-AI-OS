from binance.client import Client
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
client = Client(api_key, api_secret)


def get_binance_position(symbol: str):
    symbol = symbol.upper()
    account = client.get_account()
    balances = account["balances"]

    balance = next((b for b in balances if b["asset"] == symbol), None)
    if not balance:
        return {"error": f"{symbol} não encontrado"}

    amount = float(balance["free"]) + float(balance["locked"])
    if amount == 0:
        return {"error": f"Sem posição em {symbol}"}

    # Obter trades para calcular preço médio
    trades = client.get_my_trades(symbol=symbol + "USDT")
    if not trades:
        return {"error": "Sem histórico de trades"}

    total_qty = total_cost = 0
    for t in trades:
        qty = float(t["qty"])
        price = float(t["price"])
        if t["isBuyer"]:
            total_qty += qty
            total_cost += qty * price

    avg_price = total_cost / total_qty if total_qty else 0
    current_price = float(client.get_symbol_ticker(symbol=symbol + "USDT")["price"])

    pnl = ((current_price - avg_price) / avg_price) * 100 if avg_price else 0

    return {
        "symbol": symbol,
        "amount": round(amount, 3),
        "avg_price": round(avg_price, 4),
        "current_price": round(current_price, 4),
        "pnl_pct": round(pnl, 2),
        "status": interpret_pnl(pnl),
    }


def interpret_pnl(pct):
    if pct > 10:
        return "Lucro elevado"
    if pct > 0:
        return "Lucro leve"
    if pct < -10:
        return "Prejuízo crítico"
    return "Prejuízo leve"
