import pandas as pd
import numpy as np
import talib
from backend.services.binance_service import get_candles
from backend.config.config_scalping import SCALPING_CONFIG


async def get_latest_price(symbol: str) -> float:
    """
    Retorna o preço de fecho mais recente sem criar DataFrame.
    """
    candles = await get_candles(symbol, interval="1m", limit=1)
    return float(candles[0][4])  # Índice do close


async def get_atr(symbol: str, period: int = 14) -> float:
    candles = await get_candles(symbol, interval="1m", limit=period + 1)
    df = pd.DataFrame(
        candles, columns=["open_time", "open", "high", "low", "close", "volume"]
    )
    for col in ["high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(inplace=True)

    atr = talib.ATR(df["high"], df["low"], df["close"], timeperiod=period)
    return float(atr.dropna().iloc[-1])


async def detect_entry_signal(symbol: str):
    limit = (
        max(
            SCALPING_CONFIG["EMA_PERIOD"],
            SCALPING_CONFIG["RSI_PERIOD"],
            SCALPING_CONFIG["MACD_SLOW"],
        )
        + 5
    )
    candles = await get_candles(
        symbol, interval=SCALPING_CONFIG["CANDLE_INTERVAL"], limit=limit
    )
    df = pd.DataFrame(
        candles, columns=["open_time", "open", "high", "low", "close", "volume"]
    )
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(inplace=True)

    df["rsi"] = talib.RSI(df["close"], timeperiod=SCALPING_CONFIG["RSI_PERIOD"])
    df["ema9"] = talib.EMA(df["close"], timeperiod=SCALPING_CONFIG["EMA_PERIOD"])
    df["volume_sma"] = (
        df["volume"].rolling(window=SCALPING_CONFIG["VOLUME_SMA_PERIOD"]).mean()
    )
    df["macd"], df["macdsignal"], df["macdhist"] = talib.MACD(
        df["close"],
        fastperiod=SCALPING_CONFIG["MACD_FAST"],
        slowperiod=SCALPING_CONFIG["MACD_SLOW"],
        signalperiod=SCALPING_CONFIG["MACD_SIGNAL"],
    )

    df.dropna(inplace=True)

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    entry = (
        latest["rsi"] < SCALPING_CONFIG["RSI_ENTRY_THRESHOLD"]
        and previous["close"] < previous["ema9"]
        and latest["close"] > latest["ema9"]
        and latest["close"] > latest["open"]
        and latest["volume"] > latest["volume_sma"]
        and latest["macdhist"] > 0
    )

    entry_data = {
        "rsi": round(latest["rsi"], 2),
        "ema9": round(latest["ema9"], 4),
        "volume": round(latest["volume"], 2),
        "volume_sma": round(latest["volume_sma"], 2),
        "macdhist": round(latest["macdhist"], 5),
        "candle": "verde" if latest["close"] > latest["open"] else "vermelho",
    }

    return entry, entry_data


async def detect_exit_signal(symbol: str, position: dict):
    limit = (
        max(
            SCALPING_CONFIG["EMA_PERIOD"],
            SCALPING_CONFIG["RSI_PERIOD"],
            SCALPING_CONFIG["MACD_SLOW"],
        )
        + 5
    )
    candles = await get_candles(
        symbol, interval=SCALPING_CONFIG["CANDLE_INTERVAL"], limit=limit
    )
    df = pd.DataFrame(
        candles, columns=["open_time", "open", "high", "low", "close", "volume"]
    )
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(inplace=True)

    df["rsi"] = talib.RSI(df["close"], timeperiod=SCALPING_CONFIG["RSI_PERIOD"])
    df["macd"], df["macdsignal"], df["macdhist"] = talib.MACD(
        df["close"],
        fastperiod=SCALPING_CONFIG["MACD_FAST"],
        slowperiod=SCALPING_CONFIG["MACD_SLOW"],
        signalperiod=SCALPING_CONFIG["MACD_SIGNAL"],
    )

    df.dropna(inplace=True)
    latest = df.iloc[-1]

    if latest["rsi"] > SCALPING_CONFIG["RSI_EXIT_THRESHOLD"] and latest["macdhist"] < 0:
        return True, "RSI alto + MACD fraco"

    if latest["close"] < latest["open"] and latest["macdhist"] < 0:
        return True, "Reversão + MACD negativo"

    return False, ""
