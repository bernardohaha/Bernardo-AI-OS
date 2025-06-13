import requests

BINANCE_API_URL = "https://api.binance.com/api/v3/depth"


def fetch_order_book(symbol: str, limit: int = 20):
    params = {"symbol": symbol.upper() + "USDT", "limit": limit}
    response = requests.get(BINANCE_API_URL, params=params)
    response.raise_for_status()
    return response.json()


def analyze_order_book(symbol: str):
    try:
        data = fetch_order_book(symbol)
        bids = data["bids"]  # [[price, quantity], ...]
        asks = data["asks"]

        buy_pressure = sum(float(bid[0]) * float(bid[1]) for bid in bids)
        sell_pressure = sum(float(ask[0]) * float(ask[1]) for ask in asks)

        pressure_ratio = (
            buy_pressure / sell_pressure if sell_pressure != 0 else float("inf")
        )

        if pressure_ratio > 1.2:
            signal = "Alta pressão de compra"
        elif pressure_ratio < 0.8:
            signal = "Alta pressão de venda"
        else:
            signal = "Pressão equilibrada"

        return {
            "symbol": symbol,
            "buy_pressure": round(buy_pressure, 2),
            "sell_pressure": round(sell_pressure, 2),
            "pressure_ratio": round(pressure_ratio, 2),
            "signal": signal,
        }

    except Exception as e:
        return {"error": str(e)}
