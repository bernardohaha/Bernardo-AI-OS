from binance.client import Client
from binance.enums import *
import time
from backend.config.config_scalping import SCALPING_CONFIG

# Usa tuas env vars
API_KEY = SCALPING_CONFIG["binance_api_key"]
API_SECRET = SCALPING_CONFIG["binance_api_secret"]

client = Client(API_KEY, API_SECRET)

SLIPPAGE_TOLERANCE = SCALPING_CONFIG.get("slippage_tolerance", 0.004)  # 0.4%
FEE_RATE = 0.00075  # 0.075% por operação (média normal)


async def execute_buy_order(symbol: str, quantity: float):
    """
    Cria uma ordem de compra a mercado.
    """
    try:
        order = client.order_market_buy(symbol=symbol, quantity=quantity)

        order_id = order["orderId"]
        filled_price = sum(
            [float(f["price"]) * float(f["qty"]) for f in order["fills"]]
        ) / sum([float(f["qty"]) for f in order["fills"]])
        fee = filled_price * quantity * FEE_RATE

        return {
            "order_id": order_id,
            "price": filled_price,
            "quantity": quantity,
            "fee": fee,
        }

    except Exception as e:
        print(f"[{symbol}] ❌ Erro na compra: {e}")
        return None


async def execute_sell_order(symbol: str, quantity: float):
    """
    Cria uma ordem de venda a mercado.
    """
    try:
        order = client.order_market_sell(symbol=symbol, quantity=quantity)

        order_id = order["orderId"]
        filled_price = sum(
            [float(f["price"]) * float(f["qty"]) for f in order["fills"]]
        ) / sum([float(f["qty"]) for f in order["fills"]])
        fee = filled_price * quantity * FEE_RATE

        return {
            "order_id": order_id,
            "price": filled_price,
            "quantity": quantity,
            "fee": fee,
        }

    except Exception as e:
        print(f"[{symbol}] ❌ Erro na venda: {e}")
        return None


async def verify_order_filled(symbol: str, order_id: int):
    """
    Verifica se a ordem foi totalmente preenchida.
    """
    try:
        order = client.get_order(symbol=symbol, orderId=order_id)
        return order["status"] == "FILLED"
    except Exception as e:
        print(f"[{symbol}] ⚠️ Erro ao verificar ordem {order_id}: {e}")
        return False


async def check_slippage(expected_price: float, filled_price: float):
    """
    Verifica se a diferença entre o preço esperado e o preenchido é aceitável.
    """
    slippage = abs(filled_price - expected_price) / expected_price
    return slippage <= SLIPPAGE_TOLERANCE
