import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
    BASE_CURRENCY = "USDT"

    # Parâmetros de Análise Técnica
    RSI_PERIOD = 14
    EMA_FAST_PERIOD = 9
    EMA_SLOW_PERIOD = 21

    # Breakout logic
    BREAKOUT_THRESHOLD = 0.03  # 3% breakout acima do high


settings = Settings()
