import json
import os
from binance.spot import Spot
from backend.config import settings

# Setup cliente Binance
client = Spot(api_key=settings.BINANCE_API_KEY, api_secret=settings.BINANCE_API_SECRET)

# Ficheiro local para guardar ordens (mock ou histórico)
ORDERS_FILE = "orders.json"


# Carrega ordens guardadas localmente
def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    with open(ORDERS_FILE, "r") as f:
        return json.load(f)


# Guarda nova lista de ordens no ficheiro local
def save_orders(orders):
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=4)


# Adiciona uma nova ordem ao ficheiro local
def add_order(order):
    orders = load_orders()
    orders.append(order)
    save_orders(orders)
    return order


# Devolve as ordens mock/históricas locais
def get_orders():
    return load_orders()


# Devolve as ordens reais abertas da Binance (em tempo real)
def get_real_orders(symbol=None):
    try:
        if symbol:
            return client.get_open_orders(symbol=symbol.upper() + "USDT")
        return client.get_open_orders()
    except Exception as e:
        print(f"[ERRO] get_real_orders: {e}")
        return []
