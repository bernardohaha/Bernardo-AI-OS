SWING_CONFIG = {
    # === Indicadores Técnicos ===
    "rsi_buy_level": 30,
    "rsi_sell_level": 70,
    "rsi_period": 14,
    "ema_fast_period": 12,
    "ema_slow_period": 26,
    "atr_period": 14,
    "macd_fast_period": 12,
    "macd_slow_period": 26,
    "macd_signal_period": 9,
    "macd_threshold": 0.15,
    "indicator_limit": 100,  # Número de candles a manter/usar
    # Parâmetros de Fibonacci
    "fibonacci_threshold_pct": 0.5,  # Tolerância percentual para considerar proximidade de um nível Fibo
    # Parâmetros de Volume
    "volume_ema_period": 20,
    "volume_spike_multiplier": 1.5,  # Múltiplo da EMA do volume para considerar um spike
    # Parâmetros de Divergência RSI
    "rsi_divergence_lookback": 40,  # Período de busca de candles para detetar divergência
    # === Sistema de Scoring ===
    "min_entry_score": 0.5,  # Pontuação mínima combinada para considerar uma entrada
    "weights": {
        "rsi": 0.2,
        "ema_trend": 0.2,
        "ema_proximity": 0.15,
        "macd": 0.2,
        "pattern_strong": 0.2,
        "pattern_medium": 0.1,
        "pattern_weak": 0.05,
        "support": 0.1,
        "resistance": 0.1,
        "orderbook": 0.1,
        "volume_confirmation": 0.1,
        "pressure_neutral_penalty": 0.05,
        "fibonacci": 0.1,
        "volume_spike_confirmation": 0.1,
        "rsi_divergence_bullish": 0.25,
        "rsi_divergence_bearish": 0.25,
        "zone_broken_penalty": 0.15,
        # --- NOVOS PESOS PARA BANDAS DE BOLLINGER (Swing) ---
        "bb_above_upper": 0.1,  # Peso para preço acima da banda superior (viés de alta)
        "bb_below_lower": 0.1,  # Peso para preço abaixo da banda inferior (viés de baixa)
        "bb_between_middle_upper": 0.05,  # Peso para preço entre média e banda superior
        "bb_between_middle_lower": 0.05,  # Peso para preço entre média e banda inferior
        "bb_above_upper_reversal_potential": 0.05,  # Peso adicional se há potencial de reversão de compra
        "bb_below_lower_reversal_potential": 0.05,  # Peso adicional se há potencial de reversão de venda
        "bb_low_volatility_penalty": 0.1,  # Penalidade em caso de baixa volatilidade (bandas estreitas)
    },
    # === Entrada (ATR) ===
    "entry_distance_ema": 0.02,  # Distância percentual do preço à EMA para considerar entrada
    "entry_atr_multiples": [
        0.25,
        0.5,
    ],  # Múltiplos do ATR para calcular os pontos de entrada
    # === Take-Profit e Stop-Loss ===
    "tp_atr_multiples": [0.5, 1.0, 1.5],  # Múltiplos do ATR para calcular os TPs
    "sl_atr_multiple": 1.0,  # Múltiplo do ATR para calcular o SL inicial
    "zone_sl_buffer_atr": 0.2,  # Buffer ATR para SL ao usar zonas de suporte/resistência
    # === Gestão de Risco e Confiança ===
    "rr_critical_threshold": 1.5,  # R/R abaixo deste valor resulta em penalidade
    "rr_critical_penalty": 0.5,  # Penalidade na confiança se R/R for crítico
    "min_rr": 2.0,  # R/R mínimo aceitável para um trade
    # === Gestão de Posição ===
    "base_position": 0.01,  # Tamanho base da posição como percentagem do capital ou volume
    "max_open_trades": 3,  # Número máximo de trades abertos simultaneamente (exemplo)
    # === Memória e Execução ===
    "memory_purge_interval": 50,  # A cada quantas execuções limpar a memória antiga
    "trade_memory_retention_days": 7,  # Quantos dias para manter trades na memória
    # --- NOVO LIMIAR PARA BANDAS DE BOLLINGER (Swing) ---
    # Limiar para a largura da banda de Bollinger para considerar baixa volatilidade/compressão
    # Este valor é muito dependente do ativo e do intervalo. É um exemplo e precisa ser otimizado.
    "bb_low_volatility_threshold": 0.005,  # Exemplo: 0.5% da largura da banda para indicar baixa volatilidade
}
