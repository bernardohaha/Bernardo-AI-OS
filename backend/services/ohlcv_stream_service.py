import json
import threading
import websocket
from collections import defaultdict, deque
from datetime import datetime

MAX_CANDLES = 200
ohlcv_buffer = defaultdict(lambda: defaultdict(lambda: deque(maxlen=MAX_CANDLES)))

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
TIMEFRAMES = ["5m", "1h", "4h", "1d"]


def _build_ws_url():
    streams = [
        f"{symbol.lower()}@kline_{tf}" for symbol in SYMBOLS for tf in TIMEFRAMES
    ]
    return f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"


def _on_message(ws, message):
    try:
        data = json.loads(message)
        k = data["data"]["k"]

        symbol = data["data"]["s"]
        tf = k["i"]

        candle = {
            "timestamp": k["t"],
            "open": float(k["o"]),
            "high": float(k["h"]),
            "low": float(k["l"]),
            "close": float(k["c"]),
            "volume": float(k["v"]),
            "is_closed": k["x"],
            "source_time": datetime.utcnow().isoformat(),
        }

        if candle["is_closed"]:
            ohlcv_buffer[symbol][tf].append(candle)

    except Exception as e:
        print("[ERROR] ao processar candle:", e)


def _on_error(ws, error):
    print("[WebSocket ERROR]", error)


def _on_close(ws, code, msg):
    print("[WebSocket] Conexão encerrada:", code, msg)


def _on_open(ws):
    print("[WebSocket] Conectado ao stream de candles.")


def start_streaming_ohlcv():
    url = _build_ws_url()
    ws = websocket.WebSocketApp(
        url,
        on_open=_on_open,
        on_message=_on_message,
        on_error=_on_error,
        on_close=_on_close,
    )
    thread = threading.Thread(target=ws.run_forever, daemon=True)
    thread.start()
