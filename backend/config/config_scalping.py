SCALPING_CONFIG = {
    "SLIPPAGE_TOLERANCE": 0.004,  # 0.4%
    "MAX_POSITION_DURATION_MINUTES": 60,
    "VOLUME_SMA_PERIOD": 25,
    "CANDLE_INTERVAL": "1m",
    "RSI_PERIOD": 14,
    "EMA_PERIOD": 14,
    "MACD_FAST": 12,
    "MACD_SLOW": 26,
    "MACD_SIGNAL": 9,
    "ATR_PERIOD": 14,
    "MAX_SCALE_COUNT": 2,
    "TP_MULTIPLIER": 1.4,
    "SL_MULTIPLIER": 1.0,
    "TP_ATR_MULTIPLIER": 4,
    "SL_ATR_MULTIPLIER": 1.0,
    "VOLATILITY_FACTOR": 1.0,
    "ATR_TRAILING_STOP_MULTIPLIER": 5.0,
    # Parâmetros para a Lógica de Pontuação de Entrada
    "ENTRY_SCORE_THRESHOLD": 7,  # Pontuação mínima para entrar (de 12)
    "RSI_ENTRY_LEVEL": 45,  # Novo parâmetro para o limite de entrada do RSI
    "RSI_ENTRY_RANGE_LOW": 30,
    "RSI_ENTRY_RANGE_HIGH": 45,
    "RSI_MOMENTUM_RANGE_HIGH": 50,
    "VOLUME_CONFIRMATION_RATIO": 1.3,  # Ex: 1.5 significa 50% acima da média
    "ATR_VOLATILITY_PERIOD": 20,
    "ATR_VOLATILITY_MULTIPLIER": 1.1,
    "BREAKOUT_LOOKBACK_PERIOD": 10,  # Nº de candles para verificar a máxima
    "REVERSAL_CANDLE_ATR_MULTIPLIER": 0.8,  # Para a lógica de saída
    # Parâmetros para Bandas de Bollinger
    "BBANDS_PERIOD": 25,
    "BBANDS_STDDEV": 2.5,
}
