import json
from datetime import datetime, timedelta
from services.binance_service import get_current_price
from services import notifier_service

# Constantes do logger e anti-spam
LOG_FILE = "services/notifications_log.json"
ANTI_SPAM_HOURS = 2


# --- Funções de logger / anti-spam ---
def load_log():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def can_send_notification(symbol, recommendation):
    log = load_log()
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=ANTI_SPAM_HOURS)

    for entry in log:
        if (
            entry["symbol"] == symbol
            and entry["recommendation"] == recommendation
            and datetime.fromisoformat(entry["timestamp"]) > cutoff
        ):
            return False
    return True


def log_notification(symbol, recommendation):
    log = load_log()
    log.append(
        {
            "symbol": symbol,
            "recommendation": recommendation,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    save_log(log)


# --- Função para carregar posições reais ---
def load_positions():
    with open("services/positions.json", "r") as f:
        return json.load(f)


# --- Função para cálculo do P&L ---
def calculate_profit(entry_price, quantity, current_price):
    total_invested = entry_price * quantity
    total_current = current_price * quantity
    profit_usd = total_current - total_invested
    profit_percent = (profit_usd / total_invested) * 100
    return profit_usd, profit_percent


# --- Função principal de análise das posições ---
def analyze_positions():
    positions = load_positions()

    for symbol, data in positions.items():
        entry_price = data["entry_price"]
        quantity = data["quantity"]

        current_price = get_current_price(symbol)

        if current_price is None:
            print(f"⚠ Não foi possível obter o preço de {symbol}")
            continue

        profit_usd, profit_percent = calculate_profit(
            entry_price, quantity, current_price
        )

        print(f"📊 {symbol}: P&L {profit_percent:.2f}% | Lucro {profit_usd:.2f} USD")

        # Definir as regras de alerta
        if profit_percent >= 7:
            recommendation = f"SUGESTÃO AI OS: {symbol} - Lucro atual {profit_percent:.2f}% — Considera VENDER 🚀"
            if can_send_notification(symbol, recommendation):
                notifier_service.notify_sell(symbol, profit_percent)
                log_notification(symbol, recommendation)
            else:
                print(f"🔇 Ignorado spam para {symbol} - {recommendation}")

        elif profit_percent <= -5:
            recommendation = f"SUGESTÃO AI OS: {symbol} - Queda atual {profit_percent:.2f}% — Considera COMPRAR ⚡"
            if can_send_notification(symbol, recommendation):
                notifier_service.notify_buy(symbol, entry_price)
                log_notification(symbol, recommendation)
            else:
                print(f"🔇 Ignorado spam para {symbol} - {recommendation}")
