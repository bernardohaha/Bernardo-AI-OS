from typing import Dict
from backend.config.swing_config import SWING_CONFIG
from backend.services.indicator_utils import (
    calculate_rsi,
    calculate_ema,
    calculate_macd,
)
from backend.services.ohlcv_service import get_ohlcv_data  # lê do buffer WebSocket

TIMEFRAMES = ["5m", "1h", "4h", "1d"]


def get_indicators_multiframe(symbol: str) -> Dict[str, Dict[str, float | str]]:
    indicators = {
        "rsi": {},
        "ema_fast": {},
        "ema_slow": {},
        "macd_hist": {},
        "macd_cross": {},
    }

    macd_threshold = SWING_CONFIG["macd_threshold"]

    for tf in TIMEFRAMES:
        try:
            candles = get_ohlcv_data(
                symbol, interval=tf, limit=SWING_CONFIG.get("indicator_limit", 100)
            )
            closes = [c["close"] for c in candles if "close" in c]

            if len(closes) < 50:
                print(f"[!] Não há candles suficientes de {symbol} em {tf}.")
                continue

            # Indicadores técnicos principais
            rsi = calculate_rsi(closes, period=SWING_CONFIG["rsi_period"])
            ema_fast = calculate_ema(closes, period=SWING_CONFIG["ema_fast_period"])
            ema_slow = calculate_ema(closes, period=SWING_CONFIG["ema_slow_period"])
            macd_line, signal_line, macd_hist = calculate_macd(
                closes,
                fast_period=SWING_CONFIG["macd_fast_period"],
                slow_period=SWING_CONFIG["macd_slow_period"],
                signal_period=SWING_CONFIG["macd_signal_period"],
            )

            # Guardar valores mais recentes
            indicators["rsi"][tf] = round(rsi[-1], 2)
            indicators["ema_fast"][tf] = round(ema_fast[-1], 4)
            indicators["ema_slow"][tf] = round(ema_slow[-1], 4)
            indicators["macd_hist"][tf] = round(macd_hist[-1], 4)

            diff = macd_line[-1] - signal_line[-1]
            if abs(diff) < macd_threshold:
                indicators["macd_cross"][tf] = "neutral"
            elif diff > 0:
                indicators["macd_cross"][tf] = "bullish"
            else:
                indicators["macd_cross"][tf] = "bearish"

        except Exception as e:
            print(f"[ERRO] Falha ao calcular indicadores {symbol} @ {tf}: {e}")

    return indicators
