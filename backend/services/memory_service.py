import os
import json
import threading
from datetime import datetime, timedelta
from backend.config.swing_config import SWING_CONFIG

MEMORY_FILE = "memory_data.json"
EXECUTION_COUNTER_FILE = "execution_counter.json"
LOCK = threading.Lock()


def _load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"trades": [], "zone_tests": []}
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"[ERRO] Arquivo de memória corrompido. Reinicializando {MEMORY_FILE}")
        return {"trades": [], "zone_tests": []}


def _save_memory(data):
    with LOCK:
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)


def store_trade(symbol, side, entry, stop_loss, take_profit, confidence, rr):
    data = _load_memory()
    symbol = symbol.upper()
    data["trades"].append(
        {
            "symbol": symbol,
            "side": side,
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "confidence": confidence,
            "rr": round(rr, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    _save_memory(data)


def store_zone_test(symbol: str, level: float):
    data = _load_memory()
    symbol = symbol.upper()
    data.setdefault("zone_tests", []).append(
        {
            "symbol": symbol,
            "level": round(level, 4),
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    _save_memory(data)


def was_zone_broken(symbol: str, level: float) -> bool:
    """
    Verifica se uma zona foi recentemente testada/rompida.
    """
    data = _load_memory()
    symbol = symbol.upper()
    threshold = SWING_CONFIG.get("zone_break_tolerance", 0.5)
    lookback = SWING_CONFIG.get("zone_memory_lookback", 50)
    tests = data.get("zone_tests", [])
    for test in reversed(tests[-lookback:]):
        if test["symbol"] == symbol:
            try:
                test_level = float(test["level"])
                if abs(test_level - level) < threshold:
                    return True
            except (ValueError, TypeError):
                continue
    return False


def _load_counter():
    if not os.path.exists(EXECUTION_COUNTER_FILE):
        return 0
    try:
        with open(EXECUTION_COUNTER_FILE, "r") as f:
            return json.load(f).get("count", 0)
    except json.JSONDecodeError:
        return 0


def _save_counter(count):
    with open(EXECUTION_COUNTER_FILE, "w") as f:
        json.dump({"count": count}, f)


def increment_execution_counter():
    count = _load_counter() + 1
    _save_counter(count)
    return count


def purge_old_memory(days: int = 30, max_trades: int = 200):
    data = _load_memory()
    now = datetime.utcnow()
    limit_date = now - timedelta(days=days)

    data["trades"] = [
        t
        for t in data.get("trades", [])
        if t.get("timestamp") and datetime.fromisoformat(t["timestamp"]) > limit_date
    ][-max_trades:]

    data["zone_tests"] = [
        z
        for z in data.get("zone_tests", [])
        if z.get("timestamp") and datetime.fromisoformat(z["timestamp"]) > limit_date
    ]

    _save_memory(data)


def get_recent_trades(limit=20):
    data = _load_memory()
    return list(reversed(data.get("trades", [])[-limit:]))


def get_all_memory():
    return _load_memory()


def already_traded_recently(symbol: str, side: str, hours: int = 24) -> bool:
    """
    Verifica se já houve um trade do mesmo tipo (BUY/SELL) nesse símbolo nas últimas X horas.
    """
    recent = get_recent_trades(50)
    now = datetime.utcnow()
    for trade in recent:
        if trade["symbol"] == symbol.upper() and trade["side"] == side:
            try:
                t_time = datetime.fromisoformat(trade["timestamp"])
                if now - t_time < timedelta(hours=hours):
                    return True
            except:
                continue
    return False


# ------------------- SCALPING AGENT MEMORY -------------------


def save_trade_state(
    symbol, entry_price, quantity, entry_data, fee, tp_price, sl_price
):
    data = _load_memory()
    symbol = symbol.upper()

    scalping_entry = {
        "entry_price": entry_price,
        "quantity": quantity,
        "entry_data": entry_data,
        "fee": fee,
        "tp_price": tp_price,
        "sl_price": sl_price,
        "trailing_active": False,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Atualiza ou adiciona a entrada de scalping
    data.setdefault("scalping_trades", {})
    data["scalping_trades"][symbol] = scalping_entry
    _save_memory(data)


def get_current_position(symbol):
    data = _load_memory()
    symbol = symbol.upper()
    return data.get("scalping_trades", {}).get(symbol)


def purge_closed_trades(symbol):
    data = _load_memory()
    symbol = symbol.upper()
    if "scalping_trades" in data and symbol in data["scalping_trades"]:
        del data["scalping_trades"][symbol]
        _save_memory(data)
