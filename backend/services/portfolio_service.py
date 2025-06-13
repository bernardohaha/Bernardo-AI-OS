from backend.services.binance_service import client, get_price
from backend.services.binance_service import get_trade_history, get_current_price


def get_open_positions():
    trades_by_symbol = {}
    account = client.account()
    balances = account["balances"]

    for asset in balances:
        symbol = asset["asset"]
        total = float(asset["free"]) + float(asset["locked"])
        if total == 0 or symbol == "USDT":
            continue

        # Busca histórico de ordens para calcular preço médio
        symbol_pair = symbol + "USDT"
        trades = client.my_trades(symbol=symbol_pair)

        if not trades:
            continue

        total_qty = 0
        total_cost = 0
        orders = []

        for trade in trades:
            qty = float(trade["qty"])
            price = float(trade["price"])
            side = "BUY" if not trade["isBuyerMaker"] else "SELL"
            timestamp = trade["time"]

            orders.append({"price": price, "qty": qty, "side": side, "time": timestamp})

            if side == "BUY":
                total_qty += qty
                total_cost += qty * price

        if total_qty == 0:
            continue

        avg_entry = total_cost / total_qty
        current_price = get_price(symbol_pair)
        current_value = total * current_price
        entry_value = total * avg_entry
        pnl_value = current_value - entry_value
        pnl_pct = (pnl_value / entry_value) * 100

        trades_by_symbol[symbol] = {
            "symbol": symbol,
            "amount": total,
            "avg_entry": round(avg_entry, 4),
            "current_price": round(current_price, 4),
            "value_now": round(current_value, 2),
            "pnl_value": round(pnl_value, 2),
            "pnl_pct": round(pnl_pct, 2),
            "orders": sorted(orders, key=lambda x: x["time"], reverse=True),
        }

    return list(trades_by_symbol.values())


def build_positions(symbol: str):
    trade_data = get_trade_history(symbol)
    trades = trade_data.get("trades", [])
    current_price = get_current_price(symbol)

    positions = []

    for trade in trades:
        qty = float(trade["qty"])
        price = float(trade["price"])
        time = trade["time"]

        total_cost = qty * price
        total_now = qty * current_price
        pnl = total_now - total_cost
        pnl_pct = ((total_now / total_cost) - 1) * 100 if total_cost > 0 else 0

        positions.append(
            {
                "symbol": symbol,
                "side": "BUY" if trade["isBuyer"] else "SELL",
                "entry_price": round(price, 5),
                "current_price": round(current_price, 5),
                "quantity": qty,
                "timestamp": time,
                "profit_usd": round(pnl, 2),
                "profit_percent": round(pnl_pct, 2),
                "suggestion": "Manter",  # ← vamos atualizar com agente mais tarde
            }
        )

    return positions
