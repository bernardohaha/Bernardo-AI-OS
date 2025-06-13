from backend.services.binance_service import client, get_price
from backend.agents.supervisor_agent import supervisor_agent


def get_all_positions():
    account = client.account()
    balances = account["balances"]
    positions = {}

    for asset in balances:
        symbol = asset["asset"]
        if symbol == "USDT":
            continue

        # Agrega todos os trades reais (myTrades) da moeda
        symbol_pair = symbol + "USDT"
        try:
            trades = client.my_trades(symbol=symbol_pair)
        except Exception:
            trades = []
        if not trades:
            continue

        # MACRO
        total_qty = 0
        total_cost = 0
        buy_qty = 0
        sell_qty = 0
        for trade in trades:
            qty = float(trade["qty"])
            price = float(trade["price"])
            if trade["isBuyer"]:
                total_qty += qty
                total_cost += qty * price
                buy_qty += qty
            else:
                sell_qty += qty

        qty_current = buy_qty - sell_qty
        if qty_current == 0:
            continue  # posição fechada, pode listar só nas micro
        price_now = get_price(symbol_pair) or 0

        avg_entry = total_cost / buy_qty if buy_qty > 0 else 0
        pnl_value = (price_now - avg_entry) * qty_current
        pnl_pct = (
            (pnl_value / (avg_entry * qty_current)) * 100
            if avg_entry * qty_current > 0
            else 0
        )

        # MICRO — todas as entradas (cada trade individual, status aberta/fechada)
        # Para simplificar, mostra todas as BUY e SELL ordenadas cronologicamente
        micro = []
        for trade in sorted(trades, key=lambda t: t["time"]):
            qty = float(trade["qty"])
            price = float(trade["price"])
            side = "BUY" if trade["isBuyer"] else "SELL"
            ts = trade["time"]
            micro.append(
                {
                    "side": side,
                    "quantity": qty,
                    "price": price,
                    "value": price * qty,
                    "timestamp": ts,
                    "status": "aberta"
                    if side == "BUY" and qty_current > 0
                    else "fechada",
                }
            )

        # SUPERVISOR — recomendação global para a moeda
        try:
            supervisor = supervisor_agent(symbol)
            recomendacao = supervisor["final_recommendation"]
        except Exception:
            recomendacao = "N/A"

        # Adiciona ao dicionário final
        positions[symbol] = {
            "macro": {
                "total_investido": round(avg_entry * qty_current, 2),
                "preco_medio": round(avg_entry, 4),
                "quantidade_total": round(qty_current, 4),
                "pnl_atual": round(pnl_value, 2),
                "pnl_percent": round(pnl_pct, 2),
            },
            "micro": micro,
            "recomendacao": recomendacao,
        }

    return positions
