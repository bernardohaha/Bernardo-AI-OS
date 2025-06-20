# backend/services/scalping_pressure_service.py

import statistics  # Para calcular o desvio padrão
from backend.services.binance_service import get_order_book, get_candles

# --- Constantes de Configuração (Ajustar com Backtesting) ---
ORDERBOOK_BIAS_THRESHOLD_PERCENT = 0.05  # 5% de desequilíbrio no volume total
DELTA_VOLUME_SIGNIFICANCE_THRESHOLD_PERCENT = 0.1  # 10% do volume total do candle
CVD_SIGNIFICANCE_THRESHOLD_PERCENT = 0.2  # 20% do volume médio dos candles no lookback

# Constantes para Bandas de Bollinger no Scalping (prazos curtos)
BB_LOOKBACK_PERIOD = 20  # Período da Média Móvel e do Desvio Padrão
BB_NUM_STD_DEV = 2  # Número de desvios padrão para as bandas

# --- Funções de Análise de Pressão ---


def analyze_orderbook_desequilibrium(symbol, depth_limit=20):
    """
    Compara volume acumulado de bids e asks nos primeiros N níveis.
    Retorna um viés com base numa percentagem do volume total na profundidade.
    """
    try:
        orderbook = get_order_book(symbol)
        bids = orderbook.get("bids", [])[:depth_limit]
        asks = orderbook.get("asks", [])[:depth_limit]

        if not bids and not asks:
            return "NEUTRAL", 0.0  # Sem dados, retorna neutro

        bid_volume = sum(float(b[1]) for b in bids)
        ask_volume = sum(float(a[1]) for a in asks)

        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return "NEUTRAL", 0.0  # Evita divisão por zero

        delta = bid_volume - ask_volume
        # Normaliza o delta pelo volume total para obter uma percentagem de desequilíbrio
        normalized_delta = delta / total_volume

        if normalized_delta > ORDERBOOK_BIAS_THRESHOLD_PERCENT:
            return "BUY_BIAS", normalized_delta
        elif normalized_delta < -ORDERBOOK_BIAS_THRESHOLD_PERCENT:
            return "SELL_BIAS", normalized_delta
        else:
            return "NEUTRAL", normalized_delta
    except Exception as e:
        print(f"Erro ao analisar desequilíbrio do orderbook para {symbol}: {e}")
        return "NEUTRAL", 0.0


def calculate_delta_volume(symbol):
    """
    Calcula o delta volume (volume verde - vermelho) do último candle de 1m.
    Retorna o volume delta e o volume total do último candle.
    """
    try:
        candles = get_candles(symbol, interval="1m", limit=2)
        if not candles or len(candles) < 2:
            print(f"Dados de candles insuficientes para {symbol}.")
            return 0.0, 0.0  # Retorna 0.0 para delta_volume e volume_total

        # O último candle é o que queremos analisar (o candle mais recente, mas fechado)
        last_candle = candles[-1]
        open_price = float(last_candle[1])
        close_price = float(last_candle[4])
        volume = float(last_candle[5])  # Volume total do candle

        delta_volume = 0.0
        if close_price > open_price:
            delta_volume = volume  # Candle verde → volume de compra (proxy)
        elif close_price < open_price:
            delta_volume = -volume  # Candle vermelho → volume de venda (proxy)

        return delta_volume, volume  # Retorna o delta e o volume total do candle
    except Exception as e:
        print(f"Erro ao calcular delta volume para {symbol}: {e}")
        return 0.0, 0.0


def calculate_cvd(symbol, lookback=20):
    """
    Calcula o CVD (cumulative volume delta) com base nos últimos N candles.
    Retorna o CVD e o volume médio por candle no período.
    """
    try:
        candles = get_candles(symbol, interval="1m", limit=lookback + 1)
        if not candles or len(candles) <= lookback:
            print(
                f"Dados de candles insuficientes para CVD para {symbol} com lookback {lookback}."
            )
            return 0.0, 0.0  # Retorna 0.0 para CVD e volume médio

        cvd = 0.0
        total_volume_lookback = 0.0

        # Iterar sobre os candles relevantes para o cálculo do CVD
        for candle in candles[-lookback:]:
            open_price = float(candle[1])
            close_price = float(candle[4])
            volume = float(candle[5])

            delta = volume if close_price > open_price else -volume
            cvd += delta
            total_volume_lookback += volume

        average_volume_per_candle = (
            total_volume_lookback / lookback if lookback > 0 else 0.0
        )

        return round(cvd, 2), round(average_volume_per_candle, 2)
    except Exception as e:
        print(f"Erro ao calcular CVD para {symbol}: {e}")
        return 0.0, 0.0


def calculate_bollinger_bands(
    symbol,
    interval="1m",
    lookback_period=BB_LOOKBACK_PERIOD,
    num_std_dev=BB_NUM_STD_DEV,
):
    """
    Calcula as Bandas de Bollinger para um determinado símbolo e intervalo.
    Retorna a banda superior, banda média (SMA), banda inferior e a posição do preço atual.
    """
    try:
        # Precisamos de lookback_period + 1 para ter o candle atual e os candles históricos
        candles = get_candles(symbol, interval=interval, limit=lookback_period + 1)
        if not candles or len(candles) <= lookback_period:
            print(
                f"Dados de candles insuficientes para Bandas de Bollinger para {symbol} no intervalo {interval}."
            )
            return {
                "upper": None,
                "middle": None,
                "lower": None,
                "current_price_position": "UNKNOWN",
                "band_width": None,
            }

        # Usamos os preços de fecho para o cálculo das BB
        close_prices = [
            float(c[4]) for c in candles[-lookback_period - 1 : -1]
        ]  # Últimos 'lookback_period' candles fechados
        current_price = float(
            candles[-1][4]
        )  # Preço de fecho do candle mais recente (pode ser o atual)

        if len(close_prices) < lookback_period:  # Garante que temos dados suficientes
            print(
                f"Não há dados suficientes para calcular SMA e STD para Bandas de Bollinger."
            )
            return {
                "upper": None,
                "middle": None,
                "lower": None,
                "current_price_position": "UNKNOWN",
                "band_width": None,
            }

        # Média Móvel Simples (SMA)
        sma = sum(close_prices) / lookback_period

        # Desvio Padrão (Standard Deviation)
        std_dev = statistics.stdev(close_prices)

        # Bandas de Bollinger
        upper_band = sma + (std_dev * num_std_dev)
        lower_band = sma - (std_dev * num_std_dev)

        # Largura da banda (para avaliar volatilidade)
        band_width = upper_band - lower_band

        # Posição do preço atual em relação às bandas
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
        print(f"Erro ao calcular Bandas de Bollinger para {symbol}: {e}")
        return {
            "upper": None,
            "middle": None,
            "lower": None,
            "current_price_position": "UNKNOWN",
            "band_width": None,
        }


def generate_pressure_signal(symbol):
    """
    Gera um sinal de pressão agregando o desequilíbrio do orderbook, delta de volume, CVD e Bandas de Bollinger.
    Retorna um dicionário com os dados de pressão detalhados e o sinal agregado.
    """
    cvd, average_volume_cvd = calculate_cvd(symbol)
    delta_volume, last_candle_volume = calculate_delta_volume(symbol)
    orderbook_bias, normalized_orderbook_delta = analyze_orderbook_desequilibrium(
        symbol
    )
    bollinger_bands_data = calculate_bollinger_bands(
        symbol, interval="1m"
    )  # Para scalping, usamos 1m

    signal = "NEUTRAL"

    # Determinar a significância dos indicadores com base nos limiares definidos
    is_cvd_positive_significant = (
        cvd > 0
        and abs(cvd) > (CVD_SIGNIFICANCE_THRESHOLD_PERCENT * average_volume_cvd)
        and average_volume_cvd > 0
    )
    is_cvd_negative_significant = (
        cvd < 0
        and abs(cvd) > (CVD_SIGNIFICANCE_THRESHOLD_PERCENT * average_volume_cvd)
        and average_volume_cvd > 0
    )

    is_delta_volume_positive_significant = (
        delta_volume > 0
        and abs(delta_volume)
        > (DELTA_VOLUME_SIGNIFICANCE_THRESHOLD_PERCENT * last_candle_volume)
        and last_candle_volume > 0
    )
    is_delta_volume_negative_significant = (
        delta_volume < 0
        and abs(delta_volume)
        > (DELTA_VOLUME_SIGNIFICANCE_THRESHOLD_PERCENT * last_candle_volume)
        and last_candle_volume > 0
    )

    # Lógica de sinalização mais granular com BB
    buy_factors = 0
    sell_factors = 0

    if orderbook_bias == "BUY_BIAS":
        buy_factors += 1
    elif orderbook_bias == "SELL_BIAS":
        sell_factors += 1

    if is_delta_volume_positive_significant:
        buy_factors += 1
    elif is_delta_volume_negative_significant:
        sell_factors += 1

    if is_cvd_positive_significant:
        buy_factors += 1
    elif is_cvd_negative_significant:
        sell_factors += 1

    # --- Integração das Bandas de Bollinger no Sinal de Scalping ---
    bb_position = bollinger_bands_data.get("current_price_position")
    band_width = bollinger_bands_data.get("band_width")

    # Ações baseadas na posição do preço em relação às BBs
    if bb_position == "BELOW_LOWER":
        # Preço abaixo da banda inferior pode indicar sobre-venda ou forte queda.
        # Se houver outros sinais de compra, pode ser uma exaustão de venda.
        if buy_factors > 0:
            buy_factors += (
                1  # Aumenta a força do sinal de compra se já existirem fatores
            )
    elif bb_position == "ABOVE_UPPER":
        # Preço acima da banda superior pode indicar sobre-compra ou forte alta.
        # Se houver outros sinais de venda, pode ser uma exaustão de compra.
        if sell_factors > 0:
            sell_factors += (
                1  # Aumenta a força do sinal de venda se já existirem fatores
            )
    elif bb_position == "BETWEEN_MIDDLE_AND_LOWER":
        # Preço a recuperar para a média, pode ser um fator de compra fraco
        if delta_volume > 0:  # Se há algum volume positivo
            buy_factors += 0.5  # Fator mais fraco
    elif bb_position == "BETWEEN_MIDDLE_AND_UPPER":
        # Preço a cair para a média, pode ser um fator de venda fraco
        if delta_volume < 0:  # Se há algum volume negativo
            sell_factors += 0.5  # Fator mais fraco

    # Lógica para detetar compressão (baixa volatilidade) para potenciais rupturas
    # Um limiar para a largura da banda deve ser definido e otimizado
    # Exemplo (este limiar precisa ser calibrado para cada ativo):
    # if band_width is not None and band_width < SOME_LOW_VOLATILITY_THRESHOLD:
    #     signal = "LOW_VOLATILITY_COMPRESSION"
    #     # Numa compressão, pode-se esperar por um sinal agressivo para a direção da rutura.
    #     # Não adicionamos diretamente fatores aqui, mas podemos usar este sinal para influenciar a estratégia geral.

    # Determinar o sinal final baseado nos fatores
    if buy_factors >= 3:
        signal = "BUY_AGGRESSIVE"
    elif (
        buy_factors >= 2 and sell_factors == 0
    ):  # Pelo menos 2 fatores, e nenhum de venda
        signal = "BUY_MODERATE"
    elif (
        buy_factors >= 1 and sell_factors == 0
    ):  # Pelo menos 1 fator, e nenhum de venda
        signal = "BUY_WEAK"
    elif sell_factors >= 3:
        signal = "SELL_AGGRESSIVE"
    elif (
        sell_factors >= 2 and buy_factors == 0
    ):  # Pelo menos 2 fatores, e nenhum de compra
        signal = "SELL_MODERATE"
    elif (
        sell_factors >= 1 and buy_factors == 0
    ):  # Pelo menos 1 fator, e nenhum de compra
        signal = "SELL_WEAK"
    # Se houver conflito (buy_factors > 0 e sell_factors > 0) ou nenhum fator dominante, permanece NEUTRAL

    return {
        "cvd": cvd,
        "average_volume_cvd": average_volume_cvd,
        "delta_volume": delta_volume,
        "last_candle_volume": last_candle_volume,
        "orderbook_bias": orderbook_bias,
        "normalized_orderbook_delta": normalized_orderbook_delta,
        "bollinger_bands": bollinger_bands_data,  # Adiciona os dados das BB ao retorno
        "signal": signal,
        "buy_factors": buy_factors,
        "sell_factors": sell_factors,
    }
