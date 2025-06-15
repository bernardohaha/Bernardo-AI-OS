import numpy as np
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
    was_zone_broken,  # Este já está importado e será usado
    increment_execution_counter,
    purge_old_memory,
)
from backend.services.get_indicators_multiframe import get_indicators_multiframe
from backend.config.swing_config import SWING_CONFIG
from backend.services.price_service import get_price
from backend.services.fibonacci_service import get_fibonacci_data_from_price_series
from backend.services.fibonacci_strategy_service import evaluate_fibonacci_impact
from backend.services.volume_service import (
    calculate_volume_ema,
    is_volume_spike,
)
from backend.services.divergence_service import detect_rsi_divergence


def analyze_swing(symbol: str, candles: list):
    count = increment_execution_counter()
    if count % 50 == 0:
        purge_old_memory()

    if len(candles) < 50:
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

    closes = np.array([c["close"] for c in candles], dtype=float)
    highs = np.array([c["high"] for c in candles], dtype=float)
    lows = np.array([c["low"] for c in candles], dtype=float)
    volumes = np.array([c["volume"] for c in candles], dtype=float)

    raw_price = get_price(symbol)
    current_price = float(raw_price) if raw_price else closes[-1]

    rsi, ema_fast, ema_slow = get_indicators(closes)
    atr = calculate_atr(highs, lows, closes)
    macd_cross = get_macd_cross(closes)
    tf_indicators = get_indicators_multiframe(symbol)
    support_zone, resistance_zone = detect_zones(highs, lows, closes)
    pattern_result = detect_candlestick_patterns(candles)
    pattern_names = pattern_result.get("patterns", [])
    pattern_biases = pattern_result.get("bias", "neutro")
    pattern_strength = pattern_result.get("strength", "neutro")
    pressure = analyze_orderbook_pressure(symbol)
    price_near_ema = (
        abs(current_price - ema_slow) / current_price
        < SWING_CONFIG["entry_distance_ema"]
    )

    # === Scoring ===
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
        buy_score += 0.1
        reason_buy.append("MACD 1D bullish confirmado")
    if tf_indicators["rsi"].get("4h", 100) < SWING_CONFIG["rsi_buy_level"]:
        buy_score += 0.1
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
        sell_score += 0.1
        reason_sell.append("MACD 1D bearish confirmado")
    if tf_indicators["rsi"].get("4h", 0) > SWING_CONFIG["rsi_sell_level"]:
        sell_score += 0.1
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
        buy_score += SWING_CONFIG["weights"]["volume_spike_confirmation"]
        sell_score += SWING_CONFIG["weights"]["volume_spike_confirmation"]
        reason_buy.append("Volume spike confirmado")
        reason_sell.append("Volume spike confirmado")
    else:
        avg_volume = np.mean(volumes[-20:])
        if volumes[-1] > 0.5 * avg_volume:
            buy_score += SWING_CONFIG["weights"]["volume_confirmation"]
            sell_score += SWING_CONFIG["weights"]["volume_confirmation"]
            reason_buy.append("Volume acima da média")
            reason_sell.append("Volume acima da média")
        else:
            reason_buy.append("Volume fraco")
            reason_sell.append("Volume fraco")

    # --- PRESSÃO ---
    if pressure == "BUY_PRESSURE":
        buy_score += SWING_CONFIG["weights"]["orderbook"]
        reason_buy.append("Pressão de compra")
    elif pressure == "SELL_PRESSURE":
        sell_score += SWING_CONFIG["weights"]["orderbook"]
        reason_sell.append("Pressão de venda")
    elif pressure == "NEUTRAL":
        buy_score -= SWING_CONFIG["weights"]["pressure_neutral_penalty"]
        sell_score -= SWING_CONFIG["weights"]["pressure_neutral_penalty"]
        reason_buy.append("Pressão neutra")
        reason_sell.append("Pressão neutra")

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

    # === Decisão ===
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
        if resistance_zone:
            tp3 = min(tp3, max(resistance_zone))
        take_profits = [tp1, tp2, tp3]

        atr_sl = round(entry_1 - SWING_CONFIG["sl_atr_multiple"] * atr, 4)
        if support_zone:
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
        if resistance_zone:
            tp3 = max(tp3, min(resistance_zone))
        take_profits = [tp1, tp2, tp3]

        atr_sl = round(entry_1 + SWING_CONFIG["sl_atr_multiple"] * atr, 4)
        if resistance_zone:
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

    # Validação final
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
            final_confidence *= 0.5
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

    # Store trade
    position_size = round(SWING_CONFIG["base_position"] * final_confidence, 2)
    if rr_ratio > 0:
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
            "rsi": rsi,
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
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
        "reason": ", ".join(final_reason),
    }
