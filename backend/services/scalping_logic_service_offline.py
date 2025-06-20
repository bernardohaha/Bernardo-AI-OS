import pandas as pd

# Removi talib daqui, ele deve ser importado e os indicadores calculados no test_agent_scalping_offline.py
from backend.config.config_scalping import SCALPING_CONFIG


def detect_entry_signal_from_df(df: pd.DataFrame):
    if len(df) < 1:
        return False, {}

    latest = df.iloc[-1]

    required_indicators = ["rsi", "ema9", "volume_sma", "open", "close"]
    if not all(col in df.columns for col in required_indicators):
        print(
            "Erro: DataFrame não contém todos os indicadores necessários para detecção de entrada na função detect_entry_signal_from_df."
        )
        return False, {}

    # --- LÓGICA DE ENTRADA SIMPLIFICADA (A que deu mais trades) ---
    entry = (
        latest["rsi"] < SCALPING_CONFIG["RSI_ENTRY_THRESHOLD"]
        and latest["close"] > latest["ema9"]
        and latest["volume"] > latest["volume_sma"]
    )

    if entry:
        print("!!!!! SINAL DE ENTRADA DETETADO !!!!!")

    entry_data = {
        "rsi": round(latest["rsi"], 2),
        "ema9": round(latest["ema9"], 4),
        "volume": round(latest["volume"], 2),
        "volume_sma": round(latest["volume_sma"], 2),
        "candle": "verde" if latest["close"] > latest["open"] else "vermelho",
    }

    return entry, entry_data


def detect_exit_signal_from_df(df: pd.DataFrame, position: dict):
    if len(df) < 1:
        return False, ""

    latest = df.iloc[-1]

    # Verifica se os indicadores necessários existem no DataFrame
    required_indicators_exit = [
        "rsi",
        "close",
    ]  # Removi "macdhist" se não for usado. Mantemos "close" para a condição.
    if not all(col in df.columns for col in required_indicators_exit):
        print(
            "Erro: DataFrame não contém todos os indicadores necessários para detecção de saída na função detect_exit_signal_from_df."
        )
        return False, ""

    # --- NOVA LÓGICA DE SAÍDA SIMPLIFICADA ---
    # Saída por RSI muito alto (Take Profit Lógico)
    if latest["rsi"] > SCALPING_CONFIG["RSI_EXIT_THRESHOLD"]:
        # print(f"SINAL DE SAÍDA: RSI alto ({latest['rsi']:.2f})") # Debugging
        return True, "RSI muito alto"

    # Esta condição de saída "Reversao de preco ou RSI" (latest["close"] < position["entry_price"] and latest["rsi"] < SCALPING_CONFIG["RSI_ENTRY_THRESHOLD"])
    # foi a que causou muitas saídas rápidas e perdedoras.
    # Vou sugerir um "Stop and Reverse" (SAR) lógico mais simples, ou um "trailing stop" lógico
    # ou simplesmente confiar no SL/TP do agente.
    # Por agora, vamos mantê-lo simples e focar no RSI de saída.

    # Poderíamos adicionar aqui uma saída de emergência se o preço cair drasticamente,
    # mas o Stop Loss no test_agent_scalping_offline.py já deve cobrir isso.

    return False, ""
