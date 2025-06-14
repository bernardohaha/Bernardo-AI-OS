import requests
import html
import json
from config import settings


# Configurações fixas do teu bot (já com os valores corretos)
TELEGRAM_BOT_TOKEN = "7734880063:AAH4r12Ng_oX3IemMfB6xAIrxa96yGOHZa8"
TELEGRAM_CHAT_ID = "7277918294"


# Função genérica de envio de mensagens
def send_notification(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    escaped_message = html.escape(message)

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": escaped_message,
        "parse_mode": "HTML",
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        print("✅ Notificação enviada com sucesso!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar mensagem Telegram: {e}")


# Função específica para notificar VENDAS
def notify_sell(symbol: str, profit_percent: float):
    message = (
        f"💰 <b>SUGESTÃO AI OS:</b> "
        f"{symbol} atingiu <b>{profit_percent:.2f}%</b> de lucro — Considera <b>VENDER</b> 🚀"
    )
    send_notification(message)


# Função específica para notificar COMPRAS (opcional, mas já preparada)
def notify_buy(symbol: str, entry_price: float):
    message = (
        f"📈 <b>SINAL DE COMPRA AI:</b> "
        f"{symbol} — Entrada sugerida a <b>{entry_price:.2f} USD</b> ✅"
    )
    send_notification(message)
