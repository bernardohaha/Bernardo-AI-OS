import json
import os
from datetime import datetime

LOG_FILE = "suggestion_log.json"


def log_suggestion(data):
    timestamp = datetime.now().isoformat()
    log_entry = {"timestamp": timestamp, **data}

    # Se não existir o ficheiro cria a lista
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([log_entry], f, indent=4)
    else:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
        logs.append(log_entry)
        with open(LOG_FILE, "w") as f:
            json.dump(logs, f, indent=4)


def get_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        logs = json.load(f)
    return logs
