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
    ]
    if not all(col in df.columns for col in required_indicators):
        print("Erro: Indicadores em falta para detecção de entrada")
        return False, {}

    # Sistema de pontuação para entrada
    entry_score = 0
    max_score = 10

    # 1. Condição de Momentum (RSI) - Peso 2
    if 30 <= latest["rsi"] <= 45:  # RSI mais baixo para entrada agressiva
        entry_score += 2
    elif 45 < latest["rsi"] <= 50:
        entry_score += 1

    # 2. Tendência (EMA) - Peso 2
    if latest["close"] > latest["ema9"] and previous["close"] <= previous["ema9"]:
        # Cruzamento para cima da EMA (sinal forte)
        entry_score += 2
    elif latest["close"] > latest["ema9"]:
        # Acima da EMA (sinal moderado)
        entry_score += 1

    # 3. Volume - Peso 1
    volume_ratio = latest["volume"] / latest["volume_sma"]
    if volume_ratio >= 1.5:  # Volume 50% acima da média
        entry_score += 1
    elif volume_ratio >= 1.2:  # Volume 20% acima da média
        entry_score += 0.5

    # 4. MACD Momentum - Peso 2
    if latest["macdhist"] > 0 and latest["macdhist"] > previous["macdhist"]:
        # MACD histograma positivo e crescente
        entry_score += 2
    elif latest["macdhist"] > 0:
        # MACD histograma apenas positivo
        entry_score += 1

    # 5. Padrão de Candlestick - Peso 1
    candle_body = abs(latest["close"] - latest["open"])
    candle_range = latest["high"] - latest["low"]
    body_ratio = candle_body / candle_range if candle_range > 0 else 0

    if latest["close"] > latest["open"] and body_ratio > 0.6:
        # Candle verde com corpo grande
        entry_score += 1
    elif latest["close"] > latest["open"]:
        # Apenas candle verde
        entry_score += 0.5

    # 6. Volatilidade (ATR) - Peso 1
    # Evitar entradas em períodos de baixa volatilidade
    if latest["atr"] > df["atr"].rolling(20).mean().iloc[-1] * 1.1:
        entry_score += 1

    # 7. Confirmação de Breakout - Peso 1
    # Preço acima do máximo dos últimos 3 candles
    if len(df) >= 4:
        recent_high = df.iloc[-4:-1]["high"].max()
        if latest["close"] > recent_high:
            entry_score += 1

    # Decisão de entrada baseada na pontuação
    entry_threshold = 6  # Requer pelo menos 60% da pontuação máxima
    entry = entry_score >= entry_threshold

    if entry:
        print(
            f"!!!!! SINAL DE ENTRADA DETECTADO - Score: {entry_score}/{max_score} !!!!!"
        )

    entry_data = {
        "rsi": round(latest["rsi"], 2),
        "ema9": round(latest["ema9"], 4),
        "volume_ratio": round(volume_ratio, 2),
        "macdhist": round(latest["macdhist"], 5),
        "atr": round(latest["atr"], 4),
        "entry_score": entry_score,
        "body_ratio": round(body_ratio, 2),
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

    # 1. Saída por RSI muito alto (overbought)
    if latest["rsi"] >= 70:  # RSI mais alto para saída
        return True, f"RSI overbought ({latest['rsi']:.1f})"

    # 2. Saída por deterioração do MACD
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

    # 5. Trailing stop baseado em ATR
    if current_pnl > latest["atr"] * 0.5:  # Se lucro > 50% do ATR
        trailing_stop = current_price - (latest["atr"] * 0.3)  # Stop mais apertado
        if entry_price < trailing_stop:  # Atualiza o stop loss mental
            # Esta lógica seria melhor implementada no loop principal
            pass

    return False, ""


def calculate_dynamic_tp_sl(
    entry_price: float, atr: float, rsi: float, volatility_factor: float = 1.0
):
    """
    Calcula TP e SL dinâmicos baseados na volatilidade e condições de mercado
    """
    # Ajusta multiplicadores baseado no RSI
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

    tp = round(entry_price + (atr * tp_multiplier), 5)
    sl = round(entry_price - (atr * sl_multiplier), 5)

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
