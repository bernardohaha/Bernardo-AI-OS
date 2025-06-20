import numpy as np
import statistics  # Necessário para estatísticas se Bandas de Bollinger forem calculadas aqui, mas já está no swing_analysis_service

from backend.services.market_analysis_service import (
    get_indicators,
    calculate_atr,
    get_macd_cross,
)
from backend.services.zone_analysis_service import detect_zones
from backend.services.candlestick_patterns_service import detect_candlestick_patterns
from backend.services.orderbook_analysis_service import analyze_orderbook_pressure
from backend.services.trade_log_service import log_analysis
from backend.services.memory_service import (
    store_trade,
    was_zone_broken,
    increment_execution_counter,
    purge_old_memory,
)
from backend.services.get_indicators_multiframe import get_indicators_multiframe
from backend.config.swing_config import (
    SWING_CONFIG,
)  # Certifica-te de que SWING_CONFIG tem os novos pesos
from backend.services.price_service import get_price
from backend.services.fibonacci_service import get_fibonacci_data_from_price_series
from backend.services.fibonacci_strategy_service import evaluate_fibonacci_impact
from backend.services.volume_service import (
    calculate_volume_ema,
    is_volume_spike,
)
from backend.services.divergence_service import detect_rsi_divergence

# IMPORTANTE: Importa a função das Bandas de Bollinger do novo serviço de análise de swing
from backend.services.swing_analysis_service import calculate_bollinger_bands_swing


def analyze_swing(symbol: str, candles: list):
    """
    Realiza a análise de swing para um determinado símbolo,
    agregando múltiplos indicadores e gerando uma recomendação de trading.
    """
    count = increment_execution_counter()
    if count % 50 == 0:
        purge_old_memory()

    # Validação inicial de dados
    if len(candles) < 50:  # É bom ter candles suficientes para todos os indicadores
        return {
            "symbol": symbol,
            "recommendation": "HOLD",
            "confidence": 0,
            "entries": [],
            "take_profits": [],
            "stop_loss": None,
            "position_size": 0,
            "reason": "Poucos candles para análise",
        }

    # Preparação dos dados para indicadores
    closes = np.array(
        [float(c[4]) for c in candles], dtype=float
    )  # Ajustado para usar c[4] (close) diretamente do formato Binance
    highs = np.array(
        [float(c[2]) for c in candles], dtype=float
    )  # Ajustado para usar c[2] (high)
    lows = np.array(
        [float(c[3]) for c in candles], dtype=float
    )  # Ajustado para usar c[3] (low)
    volumes = np.array(
        [float(c[5]) for c in candles], dtype=float
    )  # Ajustado para usar c[5] (volume)

    raw_price = get_price(symbol)
    current_price = float(raw_price) if raw_price else closes[-1]

    # --- Cálculos de Indicadores Existentes ---
    rsi, ema_fast, ema_slow = get_indicators(closes)
    atr = calculate_atr(highs, lows, closes)
    macd_cross = get_macd_cross(closes)
    tf_indicators = get_indicators_multiframe(
        symbol
    )  # Indicadores de múltiplos timeframes
    support_zone, resistance_zone = detect_zones(highs, lows, closes)
    pattern_result = detect_candlestick_patterns(candles)
    pattern_names = pattern_result.get("patterns", [])
    pattern_biases = pattern_result.get("bias", "neutro")
    pattern_strength = pattern_result.get("strength", "neutro")
    pressure = analyze_orderbook_pressure(
        symbol
    )  # Assumindo que este é para swing, ou usar scalping_pressure_service
    price_near_ema = (
        abs(current_price - ema_slow) / current_price
        < SWING_CONFIG["entry_distance_ema"]
    )

    # --- Cálculo das Bandas de Bollinger para Swing ---
    # Usamos um intervalo de tempo maior, por exemplo, "4h" ou "1d"
    # A configuração (período e desvio padrão) deve ser definida em swing_analysis_service.py
    swing_bb_data = calculate_bollinger_bands_swing(
        symbol, interval="4h"
    )  # Exemplo: 4 horas

    # --- Scoring ---
    buy_score = 0
    sell_score = 0
    reason_buy = []
    reason_sell = []

    # --- BUY logic ---
    if rsi < SWING_CONFIG["rsi_buy_level"]:
        buy_score += SWING_CONFIG["weights"]["rsi"]
        reason_buy.append("RSI em sobrevenda")
    if ema_fast > ema_slow:
        buy_score += SWING_CONFIG["weights"]["ema_trend"]
        reason_buy.append("EMA rápida acima da lenta")
    if price_near_ema:
        buy_score += SWING_CONFIG["weights"]["ema_proximity"]
        reason_buy.append("Preço próximo da EMA lenta")
    if macd_cross == "bullish":
        buy_score += SWING_CONFIG["weights"]["macd"]
        reason_buy.append("Cruzamento MACD bullish")
    if tf_indicators["macd_cross"].get("1d") == "bullish":
        buy_score += 0.1  # Pode ser configurado via SWING_CONFIG
        reason_buy.append("MACD 1D bullish confirmado")
    if tf_indicators["rsi"].get("4h", 100) < SWING_CONFIG["rsi_buy_level"]:
        buy_score += 0.1  # Pode ser configurado via SWING_CONFIG
        reason_buy.append("RSI 4h em sobrevenda")
    # Zona de Suporte (se existir e não tiver sido quebrada recentemente)
    if support_zone:
        buy_score += SWING_CONFIG["weights"]["support"]
        reason_buy.append("Preço em zona de suporte")
        # Penalidade se a zona de suporte foi quebrada recentemente
        if was_zone_broken(symbol, min(support_zone), "support"):
            buy_score -= SWING_CONFIG["weights"]["zone_broken_penalty"]
            reason_buy.append("Zona de suporte recentemente quebrada (penalidade)")

    # --- SELL logic ---
    if rsi > SWING_CONFIG["rsi_sell_level"]:
        sell_score += SWING_CONFIG["weights"]["rsi"]
        reason_sell.append("RSI em sobrecompra")
    if ema_fast < ema_slow:
        sell_score += SWING_CONFIG["weights"]["ema_trend"]
        reason_sell.append("EMA rápida abaixo da lenta")
    if price_near_ema:
        sell_score += SWING_CONFIG["weights"]["ema_proximity"]
        reason_sell.append("Preço próximo da EMA lenta")
    if macd_cross == "bearish":
        sell_score += SWING_CONFIG["weights"]["macd"]
        reason_sell.append("Cruzamento MACD bearish")
    if tf_indicators["macd_cross"].get("1d") == "bearish":
        sell_score += 0.1  # Pode ser configurado via SWING_CONFIG
        reason_sell.append("MACD 1D bearish confirmado")
    if tf_indicators["rsi"].get("4h", 0) > SWING_CONFIG["rsi_sell_level"]:
        sell_score += 0.1  # Pode ser configurado via SWING_CONFIG
        reason_sell.append("RSI 4h em sobrecompra")
    # Zona de Resistência (se existir e não tiver sido quebrada recentemente)
    if resistance_zone:
        sell_score += SWING_CONFIG["weights"]["resistance"]
        reason_sell.append("Preço em zona de resistência")
        # Penalidade se a zona de resistência foi quebrada recentemente
        if was_zone_broken(symbol, max(resistance_zone), "resistance"):
            sell_score -= SWING_CONFIG["weights"]["zone_broken_penalty"]
            reason_sell.append("Zona de resistência recentemente quebrada (penalidade)")

    # --- Padrões de Velas ---
    if pattern_biases == "bullish":
        if pattern_strength == "strong":
            buy_score += SWING_CONFIG["weights"]["pattern_strong"]
            reason_buy.append(f"Padrão bullish forte: {', '.join(pattern_names)}")
        elif pattern_strength == "medium":
            buy_score += SWING_CONFIG["weights"]["pattern_medium"]
            reason_buy.append(f"Padrão bullish médio: {', '.join(pattern_names)}")
        elif pattern_strength == "weak":
            buy_score += SWING_CONFIG["weights"]["pattern_weak"]
            reason_buy.append(f"Padrão bullish fraco: {', '.join(pattern_names)}")
    elif pattern_biases == "bearish":
        if pattern_strength == "strong":
            sell_score += SWING_CONFIG["weights"]["pattern_strong"]
            reason_sell.append(f"Padrão bearish forte: {', '.join(pattern_names)}")
        elif pattern_strength == "medium":
            sell_score += SWING_CONFIG["weights"]["pattern_medium"]
            reason_sell.append(f"Padrão bearish médio: {', '.join(pattern_names)}")
        elif pattern_strength == "weak":
            sell_score += SWING_CONFIG["weights"]["pattern_weak"]
            reason_sell.append(f"Padrão bearish fraco: {', '.join(pattern_names)}")

    # --- Volume ---
    volume_ema = calculate_volume_ema(
        volumes.tolist(), SWING_CONFIG["volume_ema_period"]
    )
    is_current_volume_spike = is_volume_spike(
        volumes[-1], volume_ema, SWING_CONFIG["volume_spike_multiplier"]
    )

    if is_current_volume_spike:
        # Volume spike pode confirmar movimentos em qualquer direção
        buy_score += SWING_CONFIG["weights"]["volume_spike_confirmation"]
        sell_score += SWING_CONFIG["weights"]["volume_spike_confirmation"]
        reason_buy.append("Volume spike confirmado")
        reason_sell.append("Volume spike confirmado")
    else:
        avg_volume = np.mean(volumes[-20:])  # Média dos últimos 20 candles de volume
        if (
            volumes[-1] > 0.5 * avg_volume
        ):  # Se o volume atual é significativo (ex: >50% da média)
            buy_score += SWING_CONFIG["weights"]["volume_confirmation"]
            sell_score += SWING_CONFIG["weights"]["volume_confirmation"]
            reason_buy.append("Volume acima da média")
            reason_sell.append("Volume acima da média")
        else:
            reason_buy.append("Volume fraco")
            reason_sell.append("Volume fraco")

    # --- PRESSÃO (Assumindo que `analyze_orderbook_pressure` é para swing ou um proxy) ---
    # Se usares o `scalping_pressure_service.py` para scalping, talvez queiras um `swing_pressure_service`
    # ou ajustar a interpretação deste `pressure` para prazos mais longos.
    if pressure == "BUY_PRESSURE":
        buy_score += SWING_CONFIG["weights"]["orderbook"]
        reason_buy.append("Pressão de compra (orderbook)")
    elif pressure == "SELL_PRESSURE":
        sell_score += SWING_CONFIG["weights"]["orderbook"]
        reason_sell.append("Pressão de venda (orderbook)")
    elif pressure == "NEUTRAL":
        buy_score -= SWING_CONFIG["weights"]["pressure_neutral_penalty"]
        sell_score -= SWING_CONFIG["weights"]["pressure_neutral_penalty"]
        reason_buy.append("Pressão neutra (orderbook)")
        reason_sell.append("Pressão neutra (orderbook)")

    # --- Fibonacci ---
    fib_data = get_fibonacci_data_from_price_series(highs.tolist(), lows.tolist())
    if fib_data:
        fib_result = evaluate_fibonacci_impact(
            current_price, fib_data, SWING_CONFIG["fibonacci_threshold_pct"]
        )

        if fib_result["bias"] == "bullish":
            buy_score += SWING_CONFIG["weights"].get("fibonacci", 0.1)
            reason_buy.append(fib_result["reason"])
        elif fib_result["bias"] == "bearish":
            sell_score += SWING_CONFIG["weights"].get("fibonacci", 0.1)
            reason_sell.append(fib_result["reason"])

    # --- Divergência RSI ---
    rsi_divergence = detect_rsi_divergence(
        closes.tolist(), rsi.tolist(), SWING_CONFIG["rsi_divergence_lookback"]
    )
    if rsi_divergence["type"] == "bullish":
        buy_score += SWING_CONFIG["weights"]["rsi_divergence_bullish"]
        reason_buy.append(f"Divergência RSI bullish (idx: {rsi_divergence['index']})")
    elif rsi_divergence["type"] == "bearish":
        sell_score += SWING_CONFIG["weights"]["rsi_divergence_bearish"]
        reason_sell.append(f"Divergência RSI bearish (idx: {rsi_divergence['index']})")

    # --- INTEGRAÇÃO DAS BANDAS DE BOLLINGER (SWING) ---
    bb_position = swing_bb_data.get("current_price_position")
    band_width = swing_bb_data.get("band_width")

    if bb_position == "ABOVE_UPPER":
        # Preço acima da banda superior: forte tendência de alta ou sobrecompra.
        # Adiciona pontos de compra, mas com um peso que considere o risco de reversão.
        buy_score += SWING_CONFIG["weights"].get("bb_above_upper", 0.1)
        reason_buy.append("BB: Preço acima da banda superior")
        # Se também houver sinais de venda, pode ser exaustão de compra
        if sell_score > 0:  # Exemplo simples, pode ser mais sofisticado
            sell_score += SWING_CONFIG["weights"].get(
                "bb_above_upper_reversal_potential", 0.05
            )
            reason_sell.append("BB: Preço acima da banda superior (potencial reversão)")
    elif bb_position == "BELOW_LOWER":
        # Preço abaixo da banda inferior: forte tendência de baixa ou sobrevenda.
        sell_score += SWING_CONFIG["weights"].get("bb_below_lower", 0.1)
        reason_sell.append("BB: Preço abaixo da banda inferior")
        # Se também houver sinais de compra, pode ser exaustão de venda
        if buy_score > 0:  # Exemplo simples
            buy_score += SWING_CONFIG["weights"].get(
                "bb_below_lower_reversal_potential", 0.05
            )
            reason_buy.append("BB: Preço abaixo da banda inferior (potencial reversão)")
    elif bb_position == "BETWEEN_MIDDLE_AND_UPPER":
        # Preço entre a média e a banda superior: viés de alta.
        buy_score += SWING_CONFIG["weights"].get("bb_between_middle_upper", 0.05)
        reason_buy.append("BB: Preço entre média e banda superior (viés de alta)")
    elif bb_position == "BETWEEN_MIDDLE_AND_LOWER":
        # Preço entre a média e a banda inferior: viés de baixa.
        sell_score += SWING_CONFIG["weights"].get("bb_between_middle_lower", 0.05)
        reason_sell.append("BB: Preço entre média e banda inferior (viés de baixa)")

    # Lógica para detetar compressão (baixa volatilidade) para potenciais rupturas
    # O valor para 'bb_low_volatility_threshold' deve ser definido em SWING_CONFIG
    if band_width is not None and band_width < SWING_CONFIG.get(
        "bb_low_volatility_threshold", 0.005
    ):
        # Em baixa volatilidade, podemos penalizar trades ou esperar por confirmação forte
        buy_score -= SWING_CONFIG["weights"].get("bb_low_volatility_penalty", 0.1)
        sell_score -= SWING_CONFIG["weights"]["bb_low_volatility_penalty"]
        reason_buy.append("BB: Baixa volatilidade (bandas estreitas)")
        reason_sell.append("BB: Baixa volatilidade (bandas estreitas)")
        # Também podes considerar um sinal específico como "WAIT_FOR_BREAKOUT"

    # === Decisão Final ===
    recommendation = "HOLD"
    final_confidence = 0
    final_reason = []
    entries, take_profits = [], []
    stop_loss, rr_ratio = None, 0
    position_size = 0

    if buy_score >= SWING_CONFIG["min_entry_score"] and buy_score >= sell_score:
        recommendation = "BUY"
        final_confidence = min(1.0, round(buy_score, 2))
        final_reason = reason_buy

        entry_1 = round(current_price - SWING_CONFIG["entry_atr_multiples"][0] * atr, 4)
        entry_2 = round(current_price - SWING_CONFIG["entry_atr_multiples"][1] * atr, 4)
        entries = [entry_1, entry_2]

        tp1 = round(entry_1 + SWING_CONFIG["tp_atr_multiples"][0] * atr, 4)
        tp2 = round(entry_1 + SWING_CONFIG["tp_atr_multiples"][1] * atr, 4)
        tp3 = round(entry_1 + SWING_CONFIG["tp_atr_multiples"][2] * atr, 4)
        if resistance_zone:  # Ajusta TP para não ir além da resistência conhecida
            tp3 = min(tp3, max(resistance_zone))
        take_profits = [tp1, tp2, tp3]

        atr_sl = round(entry_1 - SWING_CONFIG["sl_atr_multiple"] * atr, 4)
        if support_zone:  # Ajusta SL para considerar suporte conhecido
            zone_sl = round(
                min(support_zone) - SWING_CONFIG["zone_sl_buffer_atr"] * atr, 4
            )
            stop_loss = min(atr_sl, zone_sl)
        else:
            stop_loss = atr_sl

    elif sell_score >= SWING_CONFIG["min_entry_score"] and sell_score > buy_score:
        recommendation = "SELL"
        final_confidence = min(1.0, round(sell_score, 2))
        final_reason = reason_sell

        entry_1 = round(current_price + SWING_CONFIG["entry_atr_multiples"][0] * atr, 4)
        entry_2 = round(current_price + SWING_CONFIG["entry_atr_multiples"][1] * atr, 4)
        entries = [entry_1, entry_2]

        tp1 = round(entry_1 - SWING_CONFIG["tp_atr_multiples"][0] * atr, 4)
        tp2 = round(entry_1 - SWING_CONFIG["tp_atr_multiples"][1] * atr, 4)
        tp3 = round(entry_1 - SWING_CONFIG["tp_atr_multiples"][2] * atr, 4)
        if support_zone:  # Ajusta TP para não ir além do suporte conhecido
            tp3 = max(
                tp3, min(support_zone)
            )  # Para venda, TP3 deve ser inferior ou igual ao suporte
        take_profits = [tp1, tp2, tp3]

        atr_sl = round(entry_1 + SWING_CONFIG["sl_atr_multiple"] * atr, 4)
        if resistance_zone:  # Ajusta SL para considerar resistência conhecida
            zone_sl = round(
                max(resistance_zone) + SWING_CONFIG["zone_sl_buffer_atr"] * atr, 4
            )
            stop_loss = max(atr_sl, zone_sl)
        else:
            stop_loss = atr_sl

    else:
        recommendation = "HOLD"
        final_confidence = min(1.0, round(max(buy_score, sell_score), 2))
        final_reason = ["Nenhuma condição atingiu o critério mínimo para BUY/SELL"]

    # Lógica de extensão Fibonacci movida para aqui, após a definição da `recommendation`
    if (
        recommendation != "HOLD"
        and fib_data
        and "extensions" in fib_data
        and fib_data["extensions"]
    ):
        valid_extensions = [
            ext
            for ext in fib_data["extensions"].values()
            if ext is not None and not np.isnan(ext)
        ]
        if valid_extensions:
            if recommendation == "BUY":
                potential_tps = [ext for ext in valid_extensions if ext > current_price]
                if potential_tps:
                    take_profits.append(round(min(potential_tps), 4))
                    take_profits = sorted(list(set(take_profits)))
            elif recommendation == "SELL":
                potential_tps = [ext for ext in valid_extensions if ext < current_price]
                if potential_tps:
                    take_profits.append(round(max(potential_tps), 4))
                    take_profits = sorted(list(set(take_profits)), reverse=True)

    # Validação final de entradas e stop loss
    if any(e <= 0 for e in entries) or (stop_loss is not None and stop_loss <= 0):
        return {
            "symbol": symbol,
            "recommendation": "HOLD",
            "confidence": final_confidence,
            "entries": [],
            "take_profits": [],
            "stop_loss": None,
            "position_size": 0,
            "reason": "Entradas ou SL inválidos",
        }

    # Cálculo e validação do Risco/Recompensa (R/R)
    try:
        risk = abs(entries[0] - stop_loss)
        reward = abs(take_profits[0] - entries[0])
        rr_ratio = reward / risk if risk > 0 else 0

        if rr_ratio <= SWING_CONFIG["rr_critical_threshold"]:
            final_confidence *= 1 - SWING_CONFIG["rr_critical_penalty"]
            return {
                "symbol": symbol,
                "recommendation": "HOLD",
                "confidence": final_confidence,
                "entries": [],
                "take_profits": [],
                "stop_loss": None,
                "position_size": 0,
                "reason": "R/R criticamente baixo",
            }

        elif rr_ratio < SWING_CONFIG["min_rr"]:
            final_confidence *= 0.5  # Reduz a confiança se R/R não for ideal
            return {
                "symbol": symbol,
                "recommendation": "HOLD",
                "confidence": final_confidence,
                "entries": [],
                "take_profits": [],
                "stop_loss": None,
                "position_size": 0,
                "reason": "R/R abaixo do mínimo",
            }

    except Exception as e:
        # Se ocorrer um erro no cálculo do R/R, mantém HOLD
        return {
            "symbol": symbol,
            "recommendation": "HOLD",
            "confidence": final_confidence,
            "entries": [],
            "take_profits": [],
            "stop_loss": None,
            "position_size": 0,
            "reason": f"Erro ao calcular R/R: {e}",
        }

    # Armazenar o trade e logar a análise
    position_size = round(SWING_CONFIG["base_position"] * final_confidence, 2)
    if rr_ratio > 0:  # Só armazena se o R/R for válido
        store_trade(
            symbol,
            recommendation,
            entries[0],
            stop_loss,
            take_profits[0],
            final_confidence,
            rr_ratio,
        )

    log_analysis(
        symbol,
        {
            "recommendation": recommendation,
            "confidence": final_confidence,
            "buy_score": buy_score,
            "sell_score": sell_score,
            "price": current_price,
            "rsi": rsi.tolist(),  # Converter numpy array para list para logging
            "ema_fast": ema_fast.tolist(),  # Converter numpy array para list para logging
            "ema_slow": ema_slow.tolist(),  # Converter numpy array para list para logging
            "macd_cross": macd_cross,
            "pattern_names": pattern_names,
            "pattern_biases": pattern_biases,
            "pattern_strength": pattern_strength,
            "pressure": pressure,
            "support_zone": support_zone,
            "resistance_zone": resistance_zone,
            "entries": entries,
            "take_profits": take_profits,
            "stop_loss": stop_loss,
            "position_size": position_size,
            "reason": final_reason,
            "fib_data": fib_data,
            "is_volume_spike": is_current_volume_spike,
            "volume_ema": volume_ema,
            "rsi_divergence_type": rsi_divergence["type"],
            "rsi_divergence_index": rsi_divergence["index"],
            "bollinger_bands_swing": swing_bb_data,  # Adicionado dados das Bandas de Bollinger
        },
    )

    return {
        "symbol": symbol,
        "recommendation": recommendation,
        "confidence": final_confidence,
        "entries": entries,
        "take_profits": take_profits,
        "stop_loss": stop_loss,
        "position_size": position_size,
        "reason": ", ".join(final_reason),  # Junta as razões numa string
    }
