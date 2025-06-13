from binance.spot import Spot
from backend.config import settings
import requests
from backend.services.trade_log_service import log_trade
from datetime import datetime

client = Spot(api_key=settings.BINANCE_API_KEY, api_secret=settings.BINANCE_API_SECRET)


def get_portfolio():
    account = client.account()
    balances = account["balances"]
    portfolio = [
        {
            "symbol": balance["asset"],
            "free": float(balance["free"]),
            "locked": float(balance["locked"]),
            "total": float(balance["free"]) + float(balance["locked"]),
        }
        for balance in balances
        if float(balance["free"]) + float(balance["locked"]) > 0
    ]
    return portfolio


def get_candles(symbol, interval="1h", limit=100):
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    klines = client.klines(symbol, interval, limit=limit)
    closes = [float(kline[4]) for kline in klines]
    return closes


def get_ohlc(symbol, interval="1h", limit=100):
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    klines = client.klines(symbol, interval, limit=limit)
    opens = [float(kline[1]) for kline in klines]
    highs = [float(kline[2]) for kline in klines]
    lows = [float(kline[3]) for kline in klines]
    closes = [float(kline[4]) for kline in klines]
    volumes = [float(kline[5]) for kline in klines]
    return {
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "closes": closes,
        "volumes": volumes,
    }


def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    r = requests.get(url)
    if r.status_code == 200:
        return float(r.json()["price"])
    else:
        return None


def get_portfolio_with_value():
    portfolio = get_portfolio()
    portfolio_with_value = []
    for asset in portfolio:
        symbol = asset["symbol"]
        total = asset["total"]
        value = None
        price = None

        # Tenta encontrar preço para moedas conhecidas
        for sufixo in ["USDT", "BUSD", "BTC", "ETH"]:
            pair = symbol + sufixo
            price = get_price(pair)
            if price is not None:
                value = float(total) * price
                break

        portfolio_with_value.append({**asset, "price": price, "value_usd": value})
    return portfolio_with_value


def get_current_price(symbol):
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    try:
        price_data = client.ticker_price(symbol=symbol)
        return float(price_data["price"])
    except Exception as e:
        print(f"Erro ao buscar preço de {symbol}: {e}")
        return None


def get_order_book(symbol: str, limit: int = 10):
    try:
        symbol = symbol.upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"
        depth = client.depth(symbol=symbol, limit=limit)
        bids = [(float(price), float(qty)) for price, qty in depth["bids"]]
        asks = [(float(price), float(qty)) for price, qty in depth["asks"]]
        return {"bids": bids, "asks": asks}
    except Exception as e:
        print(f"[ERRO] get_order_book({symbol}): {e}")
        return None


def get_candles_full(symbol, interval="1h", limit=100):
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    return client.klines(symbol, interval, limit=limit)


def get_trade_history(symbol: str):
    suffixes = ["USDT", "USDC", "BUSD", "BTC", "ETH"]
    for suffix in suffixes:
        pair = symbol.upper() + suffix
        try:
            trades = client.my_trades(symbol=pair)
            if trades:
                now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                log_trade(symbol, {"pair": pair, "timestamp": now, "trades": trades})
                return {"pair": pair, "trades": trades}
        except Exception:
            continue
    return {"error": f"Nenhum trade encontrado para {symbol} nos pares comuns."}
