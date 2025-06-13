import json
import os
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


def log_analysis(symbol: str, data: dict):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{LOG_DIR}/{symbol}_{now}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def log_trade(symbol: str, trade: dict):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{LOG_DIR}/trade_{symbol}_{now}.json"
    with open(filename, "w") as f:
        json.dump(trade, f, indent=2)
