import pandas as pd
import talib
from datetime import datetime
from backend.services.binance_service import get_candles_full as get_candles


# Padrões clássicos
BULLISH_PATTERNS = ["CDLHAMMER", "CDLENGULFING", "CDLMORNINGSTAR"]
BEARISH_PATTERNS = ["CDLSHOOTINGSTAR", "CDLDARKCLOUDCOVER", "CDLEVENINGSTAR"]


def detect_candlestick_patterns(symbol: str, interval: str = "1h", limit: int = 100):
    candles = get_candles(symbol, interval=interval, limit=limit)
    print("DEBUG CANDLES:", candles[:2])

    if not candles or len(candles) < 20:
        return {"error": "Dados insuficientes para análise de padrões."}

    try:
        # Verifica se é lista de listas (Binance API padrão)
        if isinstance(candles[0], list):
            df = pd.DataFrame(
                candles,
                columns=[
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_asset_volume",
                    "num_trades",
                    "taker_buy_base",
                    "taker_buy_quote",
                    "ignore",
                ],
            )
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]

        # Se for lista de dicionários
        elif isinstance(candles[0], dict):
            df = pd.DataFrame(candles)

            # Tenta automaticamente mapear campos alternativos
            rename_map = {
                "t": "timestamp",
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume",
            }

            df = df.rename(columns=rename_map)

            # Garante que todas as colunas necessárias estão presentes
            for col in ["timestamp", "open", "high", "low", "close", "volume"]:
                if col not in df.columns:
                    return {"error": f"Coluna '{col}' em falta nos dados recebidos."}

            df = df[["timestamp", "open", "high", "low", "close", "volume"]]

        else:
            return {"error": "Formato de dados dos candles não suportado."}

    except Exception as e:
        return {"error": f"Erro ao processar candles: {str(e)}"}

    # Processamento de datas
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df.set_index("timestamp", inplace=True)

    patterns_detected = []

    # Análise de padrões técnicos
    for pattern in BULLISH_PATTERNS + BEARISH_PATTERNS:
        func = getattr(talib, pattern, None)
        if func:
            df[pattern] = func(df["open"], df["high"], df["low"], df["close"])
            last_value = df[pattern].iloc[-1]
            if last_value != 0:
                patterns_detected.append(
                    {
                        "pattern": pattern,
                        "type": "BULLISH" if pattern in BULLISH_PATTERNS else "BEARISH",
                        "strength": abs(int(last_value)),
                    }
                )

    if not patterns_detected:
        return {"patterns": [], "implication": "NEUTRAL", "strength": "WEAK"}

    bullish = [p for p in patterns_detected if p["type"] == "BULLISH"]
    bearish = [p for p in patterns_detected if p["type"] == "BEARISH"]

    implication = "BULLISH" if len(bullish) > len(bearish) else "BEARISH"
    strength = "STRONG" if len(patterns_detected) >= 2 else "MODERATE"

    return {
        "symbol": symbol,
        "interval": interval,
        "patterns": patterns_detected,
        "implication": implication,
        "strength": strength,
    }
