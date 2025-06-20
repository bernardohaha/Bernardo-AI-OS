# backend/services/swing_analysis_service.py

import statistics
from backend.services.binance_service import (
    get_candles,
)  # Assumindo o mesmo serviço de candles

# Constantes para Bandas de Bollinger no Swing (prazos mais longos)
SWING_BB_LOOKBACK_PERIOD = 20  # Comum, mas pode ser 50 para mais suavidade
SWING_BB_NUM_STD_DEV = 2


def calculate_bollinger_bands_swing(
    symbol,
    interval="4h",
    lookback_period=SWING_BB_LOOKBACK_PERIOD,
    num_std_dev=SWING_BB_NUM_STD_DEV,
):
    """
    Calcula as Bandas de Bollinger para swing trading (prazos maiores).
    A lógica é a mesma da função de scalping, mas com o intervalo diferente.
    """
    try:
        # A lógica de cálculo é a mesma, mas com um intervalo maior
        candles = get_candles(symbol, interval=interval, limit=lookback_period + 1)
        if not candles or len(candles) <= lookback_period:
            print(
                f"Dados de candles insuficientes para Bandas de Bollinger Swing para {symbol} no intervalo {interval}."
            )
            return {
                "upper": None,
                "middle": None,
                "lower": None,
                "current_price_position": "UNKNOWN",
                "band_width": None,
            }

        close_prices = [float(c[4]) for c in candles[-lookback_period - 1 : -1]]
        current_price = float(candles[-1][4])

        if len(close_prices) < lookback_period:
            print(
                f"Não há dados suficientes para calcular SMA e STD para Bandas de Bollinger Swing."
            )
            return {
                "upper": None,
                "middle": None,
                "lower": None,
                "current_price_position": "UNKNOWN",
                "band_width": None,
            }

        sma = sum(close_prices) / lookback_period
        std_dev = statistics.stdev(close_prices)

        upper_band = sma + (std_dev * num_std_dev)
        lower_band = sma - (std_dev * num_std_dev)
        band_width = upper_band - lower_band

        current_price_position = "MIDDLE"
        if current_price > upper_band:
            current_price_position = "ABOVE_UPPER"
        elif current_price < lower_band:
            current_price_position = "BELOW_LOWER"
        elif current_price >= sma:
            current_price_position = "BETWEEN_MIDDLE_AND_UPPER"
        elif current_price < sma:
            current_price_position = "BETWEEN_MIDDLE_AND_LOWER"

        return {
            "upper": round(upper_band, 4),
            "middle": round(sma, 4),
            "lower": round(lower_band, 4),
            "current_price_position": current_price_position,
            "band_width": round(band_width, 4),
        }
    except Exception as e:
        print(f"Erro ao calcular Bandas de Bollinger Swing para {symbol}: {e}")
        return {
            "upper": None,
            "middle": None,
            "lower": None,
            "current_price_position": "UNKNOWN",
            "band_width": None,
        }


def generate_swing_signal(symbol):
    """
    Exemplo de função para gerar um sinal de swing, incluindo Bandas de Bollinger.
    Esta função seria mais complexa, incluindo outros indicadores de tendência (e.g., MACD, RSI).
    """
    bb_data = calculate_bollinger_bands_swing(
        symbol, interval="4h"
    )  # Exemplo de intervalo para swing

    # Lógica de sinal para swing com BB:
    # 1. Ruptura das Bandas:
    #    - Se o preço fechar acima da banda superior após um período de consolidação: sinal de compra.
    #    - Se o preço fechar abaixo da banda inferior após um período de consolidação: sinal de venda.
    # 2. Caminhar pelas Bandas (Walking the Bands):
    #    - Se o preço "caminha" ao longo da banda superior: tendência de alta forte.
    #    - Se o preço "caminha" ao longo da banda inferior: tendência de baixa forte.
    # 3. Retorno à Média (Mean Reversion):
    #    - Se o preço toca uma banda externa e reverte para a SMA: possível entrada contra a tendência de curto prazo.
    # 4. Largura da Banda:
    #    - Bandas estreitas: baixa volatilidade, potencial para grande movimento.
    #    - Bandas largas: alta volatilidade.

    swing_signal = "NEUTRAL"

    if bb_data["current_price_position"] == "ABOVE_UPPER":
        # Se preço acima da banda superior, pode indicar forte tendência de alta ou sobrecompra
        # (requer outros indicadores para confirmação)
        swing_signal = "STRONG_UPTREND_POSSIBLE_OVERBOUGHT"
    elif bb_data["current_price_position"] == "BELOW_LOWER":
        # Se preço abaixo da banda inferior, pode indicar forte tendência de baixa ou sobrevenda
        # (requer outros indicadores para confirmação)
        swing_signal = "STRONG_DOWNTREND_POSSIBLE_OVERSOLD"
    elif bb_data["current_price_position"] == "BETWEEN_MIDDLE_AND_UPPER":
        swing_signal = "UPTREND_BIAS"
    elif bb_data["current_price_position"] == "BETWEEN_MIDDLE_AND_LOWER":
        swing_signal = "DOWNTREND_BIAS"

    # Exemplo simples de como a largura da banda pode ser usada:
    # if bb_data["band_width"] is not None and bb_data["band_width"] < SOME_SWING_LOW_VOL_THRESHOLD:
    #     swing_signal = "CONSOLIDATION_WAIT_FOR_BREAKOUT"

    return {
        "bollinger_bands": bb_data,
        "signal": swing_signal,
        # Adicionar outros dados de swing aqui (e.g., RSI, MACD)
    }
