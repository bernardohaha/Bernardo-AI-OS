import json
import os
from backend.services.binance_service import get_price

ORDERS_FILE = os.path.join(os.path.dirname(__file__), "..", "orders.json")


def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    with open(ORDERS_FILE, "r") as f:
        return json.load(f)


def save_orders(orders):
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)


def execute_orders():
    orders = load_orders()
    updated = False

    for order in orders:
        if order["status"] != "OPEN":
            continue

        symbol = order["symbol"]
        price_target = order["price"]
        current_price = get_price(symbol)

        if current_price is None:
            print(f"Não foi possível obter preço para {symbol}.")
            continue

        print(f"Verificando {symbol}: atual {current_price} | alvo {price_target}")

        if order["side"] == "SELL" and current_price >= price_target:
            order["status"] = "FILLED"
            print(f"Ordem de VENDA executada para {symbol}")

        elif order["side"] == "BUY" and current_price <= price_target:
            order["status"] = "FILLED"
            print(f"Ordem de COMPRA executada para {symbol}")

        updated = True

    if updated:
        save_orders(orders)
