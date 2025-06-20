# backend/backtesting/test_agent_scalping_offline.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pandas as pd
import talib  # Importar talib aqui
import matplotlib.pyplot as plt

from backend.agents.agent_scalping_offline import agent_scalping_offline
from backend.backtesting.data_loader import load_csv_candles
from backend.backtesting.utils.metrics import (
    generate_equity_curve,
    profit_factor,
    win_rate,
    average_pnl,
    max_drawdown,
)
from backend.config.config_scalping import SCALPING_CONFIG


def plot_backtest_results(df: pd.DataFrame, trades_df: pd.DataFrame):
    """
    Função para plotar os resultados do backtest, incluindo indicadores e trades.
    Assume que o df já tem os indicadores calculados.
    """
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(18, 12), sharex=True)

    # Gráfico de Preço e EMA
    ax1.plot(df.index, df["close"], label="Preço de Fecho", color="blue")
    ax1.plot(df.index, df["ema9"], label="EMA9", color="red", linestyle="--")

    # Plotar entradas
    entry_trades = trades_df[trades_df["type"] == "entry"]
    ax1.scatter(
        entry_trades["time"],
        entry_trades["price"],
        marker="^",
        color="green",
        s=100,
        label="Entrada",
        zorder=5,
    )
    # Plotar saídas
    exit_trades = trades_df[trades_df["type"] == "exit"]
    ax1.scatter(
        exit_trades["time"],
        exit_trades["price"],
        marker="v",
        color="red",
        s=100,
        label="Saída",
        zorder=5,
    )

    ax1.set_title("Preço e EMA9 com Sinais de Trade", fontsize=14)
    ax1.set_ylabel("Preço", fontsize=12)
    ax1.legend()
    ax1.grid(True, linestyle=":", alpha=0.7)

    # Gráfico de RSI
    ax2.plot(df.index, df["rsi"], label="RSI", color="purple")
    ax2.axhline(
        SCALPING_CONFIG["RSI_ENTRY_THRESHOLD"],
        color="red",
        linestyle=":",
        alpha=0.8,
        label=f"RSI Entrada ({SCALPING_CONFIG['RSI_ENTRY_THRESHOLD']})",
    )
    ax2.axhline(
        SCALPING_CONFIG["RSI_EXIT_THRESHOLD"],
        color="green",
        linestyle=":",
        alpha=0.8,
        label=f"RSI Saída ({SCALPING_CONFIG['RSI_EXIT_THRESHOLD']})",
    )
    ax2.set_title("Índice de Força Relativa (RSI)", fontsize=14)
    ax2.set_ylabel("RSI", fontsize=12)
    ax2.set_ylim(0, 100)
    ax2.legend()
    ax2.grid(True, linestyle=":", alpha=0.7)

    # Gráfico de Volume
    ax3.bar(df.index, df["volume"], label="Volume", color="grey", alpha=0.7)
    ax3.plot(
        df.index, df["volume_sma"], label="Volume SMA", color="orange", linestyle="--"
    )
    ax3.set_title("Volume de Negociação", fontsize=14)
    ax3.set_ylabel("Volume", fontsize=12)
    ax3.legend()
    ax3.grid(True, linestyle=":", alpha=0.7)

    # Gráfico de MACD Histograma
    colors_macd = ["green" if x > 0 else "red" for x in df["macdhist"]]
    ax4.bar(df.index, df["macdhist"], label="MACD Histograma", color=colors_macd)
    ax4.axhline(0, color="black", linestyle="-", linewidth=0.8)
    ax4.set_title("MACD Histograma", fontsize=14)
    ax4.set_ylabel("Valor", fontsize=12)
    ax4.legend()
    ax4.grid(True, linestyle=":", alpha=0.7)

    plt.xlabel("Data/Hora", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()


def run_backtest():
    candles = load_csv_candles("SUIUSDT", "1m", folder="scalping", limit=1440 * 9)
    df = pd.DataFrame(candles)

    # 1. Converter open_time para datetime e definir como índice
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ns", errors="coerce")
    df.set_index("open_time", inplace=True)
    # LINHA REMOVIDA: df.dropna(subset=["open_time"], inplace=True)
    df.sort_index(inplace=True)

    # 2. Garantir que as colunas de preço e volume são numéricas
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 3. Remover linhas com NaNs nas colunas críticas ANTES de calcular indicadores
    df.dropna(subset=["open", "high", "low", "close", "volume"], inplace=True)

    # 4. Verificar se o DataFrame tem dados suficientes para os indicadores
    min_candles_for_indicators = max(
        SCALPING_CONFIG["RSI_PERIOD"],
        SCALPING_CONFIG["EMA_PERIOD"],
        SCALPING_CONFIG["VOLUME_SMA_PERIOD"],
        SCALPING_CONFIG["MACD_SLOW"] + SCALPING_CONFIG["MACD_SIGNAL"],
        SCALPING_CONFIG.get("ATR_PERIOD", 14),
    )
    if len(df) < min_candles_for_indicators:
        print(
            f"Erro: Dados insuficientes para calcular todos os indicadores após a limpeza inicial."
        )
        print(
            f"Tamanho do DataFrame: {len(df)}. Mínimo necessário baseado nos períodos: {min_candles_for_indicators}"
        )
        return {
            "final_capital": 1000,
            "profit": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "avg_pnl": 0,
            "total_trades": 0,
        }

    # 5. CALCULAR TODOS OS INDICADORES AQUI NO DATAFRAME PRINCIPAL (df)
    # Convert Pandas Series to NumPy array with float64 dtype for TA-Lib
    close_prices = df["close"].values.astype(float)
    high_prices = df["high"].values.astype(float)
    low_prices = df["low"].values.astype(float)

    df["rsi"] = talib.RSI(close_prices, timeperiod=SCALPING_CONFIG["RSI_PERIOD"])
    df["ema9"] = talib.EMA(close_prices, timeperiod=SCALPING_CONFIG["EMA_PERIOD"])
    df["volume_sma"] = (
        df["volume"].rolling(window=SCALPING_CONFIG["VOLUME_SMA_PERIOD"]).mean()
    )
    df["macd"], df["macdsignal"], df["macdhist"] = talib.MACD(
        close_prices,
        fastperiod=SCALPING_CONFIG["MACD_FAST"],
        slowperiod=SCALPING_CONFIG["MACD_SLOW"],
        signalperiod=SCALPING_CONFIG["MACD_SIGNAL"],
    )
    df["atr"] = talib.ATR(
        high_prices,
        low_prices,
        close_prices,
        timeperiod=SCALPING_CONFIG.get("ATR_PERIOD", 14),
    )

    # 6. Remover NaNs que surgem no INÍCIO após o cálculo dos indicadores (primeiras N linhas)
    df.dropna(inplace=True)

    # 7. Verificar novamente se o DataFrame tem dados suficientes para a lógica do agente
    if len(df) < 2:  # Mínimo de 2 candles para previous e latest na lógica de sinal
        print(
            "Erro: Dados insuficientes após o cálculo e limpeza dos indicadores. Mínimo de 2 candles necessários para a lógica de entrada/saída."
        )
        return {
            "final_capital": 1000,
            "profit": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "avg_pnl": 0,
            "total_trades": 0,
        }

    trades = []
    equity = 1000.0
    position = None

    plot_trades_events = []

    # lookback_window_agent define quantos candles são passados para a lógica do agente.
    # Como os indicadores já estão no DF e a lógica de sinal só precisa de latest e previous, 2 é o suficiente.
    lookback_window_agent = 2

    for i in range(len(df)):
        if (
            i < lookback_window_agent - 1
        ):  # Garante que temos pelo menos N candles para formar a janela
            continue

        # current_window_for_agent agora contém a fatia do DataFrame COM os indicadores
        current_window_for_agent = df.iloc[i - (lookback_window_agent - 1) : i + 1]

        current_price = current_window_for_agent.iloc[-1]["close"]
        current_time = current_window_for_agent.index[-1]

        result = agent_scalping_offline("SUIUSDT", current_window_for_agent, position)

        if not position and result["entry"]:
            position = {
                "entry_price": result["entry_price"],
                "tp": result["tp"],
                "sl": result["sl"],
                "entry_time": current_time,
            }
            print(
                f"ENTRADA em {current_time} | Preço: {position['entry_price']:.4f} | TP: {position['tp']:.4f} | SL: {position['sl']:.4f}"
            )
            plot_trades_events.append(
                {"time": current_time, "price": current_price, "type": "entry"}
            )

        elif position:
            if current_price >= position["tp"]:
                pnl = position["tp"] - position["entry_price"]
                trades.append(pnl)
                equity += pnl
                print(
                    f"SAÍDA por TP em {current_time} | Preço: {current_price:.4f} | PnL: {pnl:.4f}"
                )
                plot_trades_events.append(
                    {"time": current_time, "price": current_price, "type": "exit"}
                )
                position = None
            elif current_price <= position["sl"]:
                pnl = position["sl"] - position["entry_price"]
                trades.append(pnl)
                equity += pnl
                print(
                    f"SAÍDA por SL em {current_time} | Preço: {current_price:.4f} | PnL: {pnl:.4f}"
                )
                plot_trades_events.append(
                    {"time": current_time, "price": current_price, "type": "exit"}
                )
                position = None
            else:
                agent_exit_signal, reason = result["exit"], result["reason"]
                if agent_exit_signal:
                    pnl = current_price - position["entry_price"]
                    trades.append(pnl)
                    equity += pnl
                    print(
                        f"SAÍDA por {reason} em {current_time} | Preço: {current_price:.4f} | PnL: {pnl:.4f}"
                    )
                    plot_trades_events.append(
                        {"time": current_time, "price": current_price, "type": "exit"}
                    )
                    position = None

    trades_df_for_plot = pd.DataFrame(plot_trades_events)

    equity_curve = generate_equity_curve(1000, trades)

    # Plotar os resultados no final
    plot_backtest_results(df, trades_df_for_plot)

    return {
        "final_capital": equity,
        "profit": equity - 1000,
        "win_rate": win_rate(trades),
        "profit_factor": profit_factor(trades),
        "max_drawdown": max_drawdown(equity_curve),
        "avg_pnl": average_pnl(trades),
        "total_trades": len(trades),
    }


if __name__ == "__main__":
    results = run_backtest()
    print("\n--- Resultados do Backtest ---")
    for key, value in results.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
