import requests
import json

TELEGRAM_BOT_TOKEN = "7734880063:AAH4r12Ng_oX3IemMfB6xAIrxa96yGOHZa8"
TELEGRAM_CHAT_ID = 7277918294  # <- já confirmado pelo getUpdates


def send_test_message():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🚀 Teste final: Bernardo Trading Advisor está online!",
        "parse_mode": "HTML",
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, data=json.dumps(payload), headers=headers)

    print(response.status_code)
    print(response.text)


send_test_message()
