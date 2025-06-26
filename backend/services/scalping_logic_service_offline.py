# backend/services/scalping_logic_service_offline.py

import pandas as pd
import numpy as np
from backend.config.config_scalping import SCALPING_CONFIG


def detect_entry_signal_from_df(df: pd.DataFrame):
    """
    Lógica de entrada otimizada com múltiplas condições e pontuação
    """
    if len(df) < 2:
        return False, {}

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    required_indicators = [
        "rsi",
        "ema9",
        "volume_sma",
        "macdhist",
        "atr",
        "open",
        "close",
        "high",
        "low",
        "lowerband",
    ]
    if not all(col in df.columns for col in required_indicators):
        print("Erro: Indicadores em falta para detecção de entrada")
        return (
            False,
            {},
        )  # Retorna um resultado sem entrada se os indicadores não estiverem disponíveis

    # Sistema de pontuação para entrada (LÓGICA SIMPLIFICADA)
    entry_score = 0
    max_score = 2  # Agora baseado em 2 condições para manter a formatação do print

    # Nova Lógica de Entrada Simplificada: Comprar se preço estiver abaixo da BBand inferior E RSI baixo
    # 1. Condição de Bandas de Bollinger e RSI
    if (
        "lowerband" in latest
        and latest["close"] < latest["lowerband"]
        and latest["rsi"] < SCALPING_CONFIG["RSI_ENTRY_LEVEL"]
    ):
        entry_score = 2  # Apenas para que o score seja 2/2 quando a condição é metida

    # Decisão de entrada baseada na pontuação
    entry_threshold = 2  # Requer que ambas as condições sejam metidas
    entry = entry_score >= entry_threshold

    if entry:
        print(
            f"!!!!! SINAL DE ENTRADA DETECTADO - Score: {entry_score}/{max_score} !!!!!"
        )

    entry_data = {
        "rsi": round(latest["rsi"], 2),
        "ema9": round(latest["ema9"], 4),
        "macdhist": round(latest["macdhist"], 5),
        "atr": round(latest["atr"], 4),
        "entry_score": entry_score,
        "candle": "verde" if latest["close"] > latest["open"] else "vermelho",
    }

    return entry, entry_data


def detect_exit_signal_from_df(df: pd.DataFrame, position: dict):
    """
    Lógica de saída otimizada com trailing stop e múltiplas condições
    """
    if len(df) < 2:
        return False, ""

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    required_indicators = ["rsi", "macdhist", "close", "ema9", "atr"]
    if not all(col in df.columns for col in required_indicators):
        print("Erro: Indicadores em falta para detecção de saída")
        return False, ""

    current_price = latest["close"]
    entry_price = position["entry_price"]
    current_pnl = current_price - entry_price

    # 1. Saída por deterioração do MACD
    if (
        latest["macdhist"] < 0 and previous["macdhist"] > 0 and current_pnl > 0
    ):  # Só sai se estiver em lucro
        return True, "MACD negativo (com lucro)"

    # 3. Saída por quebra da EMA (stop loss dinâmico)
    if (
        current_price < latest["ema9"]
        and previous["close"] >= previous["ema9"]
        and current_pnl < 0
    ):  # Só sai se estiver em prejuízo
        return True, "Quebra EMA (stop loss)"

    # 4. Saída por reversão forte (candle vermelho grande)
    if latest["close"] < latest["open"]:
        candle_body = abs(latest["close"] - latest["open"])
        avg_atr = df["atr"].rolling(10).mean().iloc[-1]
        if candle_body > avg_atr * 0.8:  # Candle vermelho > 80% do ATR médio
            return True, "Reversão forte"

    return False, ""


def calculate_dynamic_tp_sl(
    entry_price: float, atr: float, rsi: float, volatility_factor: float = 1.0
):
    # Ajusta multiplicadores baseado no RSI para TP/SL
    # Estes multiplicadores devem ser ajustados e testados para o scalping
    # Valores menores podem ser mais adequados para capturar pequenos lucros rapidamente

    if rsi <= 35:  # Muito oversold - maior potencial de alta
        tp_multiplier = 2.0
        sl_multiplier = 0.8
    elif rsi <= 45:  # Moderadamente oversold
        tp_multiplier = 1.6
        sl_multiplier = 0.9
    else:  # RSI normal
        tp_multiplier = 1.3
        sl_multiplier = 1.0

    # Ajusta pela volatilidade
    tp_multiplier *= volatility_factor
    sl_multiplier *= volatility_factor
    # Usar SCALPING_CONFIG para definir multiplicadores base ou limites
    tp = round(
        entry_price
        + (atr * tp_multiplier * SCALPING_CONFIG.get("TP_ATR_MULTIPLIER", 1.0)),
        5,
    )
    sl = round(
        entry_price
        - (atr * sl_multiplier * SCALPING_CONFIG.get("SL_ATR_MULTIPLIER", 1.0)),
        5,
    )

    return tp, sl


def should_scale_position(df: pd.DataFrame, position: dict, max_scale_count: int = 2):
    """
    Determina se deve aumentar a posição (pyramiding/scaling)
    """
    if len(df) < 5:
        return False, 0

    latest = df.iloc[-1]
    entry_price = position["entry_price"]
    current_price = latest["close"]

    # Só escala se estiver em lucro
    if current_price <= entry_price:
        return False, 0

    # Só escala se RSI ainda estiver favorável
    if latest["rsi"] > 60:
        return False, 0

    # Só escala se MACD ainda estiver positivo
    if latest["macdhist"] <= 0:
        return False, 0

    # Calcula quantas vezes já escalou
    current_scale_count = position.get("scale_count", 0)
    if current_scale_count >= max_scale_count:
        return False, 0

    # Verifica se o preço subiu o suficiente para nova entrada
    profit_ratio = (current_price - entry_price) / entry_price
    min_profit_for_scale = 0.005 * (current_scale_count + 1)  # 0.5%, 1%, 1.5%...

    if profit_ratio >= min_profit_for_scale:
        scale_size = 0.5  # 50% da posição original
        return True, scale_size

    return False, 0
