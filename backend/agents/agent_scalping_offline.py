# backend/agents/agent_scalping_offline.py

from backend.services.scalping_logic_service_offline import (
    detect_entry_signal_from_df,
    detect_exit_signal_from_df,
)
from backend.services.stop_exit_logic import calculate_take_profit, calculate_stop_loss


def agent_scalping_offline(symbol, df, position=None):
    """
    Versão offline do agent de scalping que analisa um DataFrame local.
    """
    entry_signal, entry_data = detect_entry_signal_from_df(df)
    result = {
        "entry": False,
        "exit": False,
        "entry_price": None,
        "tp": None,
        "sl": None,
        "reason": "",
        "entry_data": entry_data,
    }

    if position:
        exit_signal, reason = detect_exit_signal_from_df(df, position)
        if exit_signal:
            result.update({"exit": True, "reason": reason})
        return result

    if entry_signal:
        price = df.iloc[-1]["close"]
        # O ATR JÁ FOI CALCULADO no test_agent_scalping_offline.py
        # Apenas acedemos a ele aqui.
        if "atr" not in df.columns:
            print(
                "Erro: ATR não encontrado no DataFrame. Por favor, calcule o ATR antes de chamar o agente."
            )
            return result  # Retorna um resultado sem entrada se o ATR não estiver disponível

        atr = df.iloc[-1]["atr"]  # Acessa o ATR já calculado na última linha do DF
        tp = calculate_take_profit(price, atr)
        sl = calculate_stop_loss(price, atr)

        result.update(
            {
                "entry": True,
                "entry_price": price,
                "tp": tp,
                "sl": sl,
            }
        )

    return result
