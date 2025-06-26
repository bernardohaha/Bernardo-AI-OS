# backend/backtesting/test_agent_scalping_offline.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pandas as pd
import talib  # Importar talib aqui
import matplotlib.pyplot as plt
import numpy as np  # Adicionar import para numpy

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

# Importar as novas funções
from backend.services.scalping_logic_service_offline import (
    calculate_dynamic_tp_sl,
    should_scale_position,
)


def plot_backtest_results(
    df: pd.DataFrame, trades_df: pd.DataFrame, trailing_stop_df: pd.DataFrame
):
    """
    Função para plotar os resultados do backtest, incluindo indicadores e trades.
    Assume que o df já tem os indicadores calculados.
    """
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(18, 12), sharex=True)

    # Gráfico de Preço e EMA
    ax1.plot(df.index, df["close"], label="Preço de Fecho", color="blue")
    ax1.plot(df.index, df["ema9"], label="EMA9", color="red", linestyle="--")
    # Plotar Bandas de Bollinger
    ax1.plot(df.index, df["upperband"], label="BBand Superior", color="grey", alpha=0.5)
    ax1.plot(
        df.index,
        df["middleband"],
        label="BBand Média",
        color="grey",
        linestyle="--",
        alpha=0.5,
    )
    ax1.plot(df.index, df["lowerband"], label="BBand Inferior", color="grey", alpha=0.5)
    ax1.fill_between(
        df.index, df["upperband"], df["lowerband"], color="grey", alpha=0.1
    )

    # Plotar entradas
    entry_trades = trades_df[trades_df["type"] == "entry"]
    ax1.scatter(
        entry_trades.index,
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
        exit_trades.index,
        exit_trades["price"],
        marker="v",
        color="red",
        s=100,
        label="Saída",
        zorder=5,
    )
    ax1.plot(
        trailing_stop_df.index,
        trailing_stop_df["price"],
        label="Trailing Stop",
        color="orange",
        linestyle="-.",
    )

    ax1.set_title("Preço de Fecho e EMA9 com Sinais de Trade")
    ax1.set_ylabel("Preço")
    ax1.legend()
    ax1.grid(True)

    # Gráfico RSI
    ax2.plot(df.index, df["rsi"], label="RSI", color="purple")
    ax2.set_title("RSI")
    ax2.set_ylabel("Valor")
    ax2.legend()
    ax2.grid(True)

    # Gráfico MACD
    ax3.plot(df.index, df["macd"], label="MACD", color="blue")
    ax3.plot(df.index, df["macdsignal"], label="MACD Signal", color="red")
    ax3.bar(
        df.index,
        df["macdhist"],
        label="MACD Histograma",
        color="gray",
        alpha=0.7,
    )
    ax3.axhline(0, color="black", linestyle="--")
    ax3.set_title("MACD")
    ax3.set_ylabel("Valor")
    ax3.legend()
    ax3.grid(True)

    # Gráfico de Volume
    ax4.bar(df.index, df["volume"], label="Volume", color="orange", alpha=0.7)
    ax4.plot(
        df.index,
        df["volume_sma"],
        label="Volume SMA",
        color="blue",
        linestyle="--",
    )
    ax4.set_title("Volume")
    ax4.set_xlabel("Data")
    ax4.set_ylabel("Volume")
    ax4.legend()
    ax4.grid(True)

    plt.tight_layout()
    plt.show()


def run_backtest():
    candles = load_csv_candles("SUIUSDT", "1m", folder="scalping", limit=1440 * 9)
    df = pd.DataFrame(candles)

    trades = []
    initial_capital = 1000.0
    equity = initial_capital
    trade_percentage = 0.20  # 20% do capital por trade
    position = None
    plot_trades_events = []  # Para os teus plots
    plot_trailing_stop_events = []  # Para os dados do trailing stop

    # Adicionar colunas de tempo para plotagem
    # Os timestamps parecem estar em microssegundos, dividir por 1000 para obter milissegundos
    df["open_time"] = pd.to_datetime(
        df["open_time"] / 1000, unit="ms"
    )  # Converte o timestamp original para datetime para o plot
    df.set_index("open_time", inplace=True)  # Define open_time como index para o plot

    # Pré-calcular todos os indicadores para o DataFrame completo
    # Converter Series do Pandas para arrays NumPy com dtype float64 para compatibilidade com TA-Lib
    close_prices = df["close"].values.astype(np.float64)
    high_prices = df["high"].values.astype(np.float64)
    low_prices = df["low"].values.astype(np.float64)

    df["ema9"] = talib.EMA(close_prices, timeperiod=SCALPING_CONFIG["EMA_PERIOD"])
    df["rsi"] = talib.RSI(close_prices, timeperiod=SCALPING_CONFIG["RSI_PERIOD"])
    df["macd"], df["macdsignal"], df["macdhist"] = talib.MACD(
        close_prices,
        fastperiod=SCALPING_CONFIG["MACD_FAST"],
        slowperiod=SCALPING_CONFIG["MACD_SLOW"],
        signalperiod=SCALPING_CONFIG["MACD_SIGNAL"],
    )
    df["atr"] = talib.ATR(
        high_prices, low_prices, close_prices, timeperiod=SCALPING_CONFIG["ATR_PERIOD"]
    )
    df["volume_sma"] = (
        df["volume"].rolling(window=SCALPING_CONFIG["VOLUME_SMA_PERIOD"]).mean()
    )
    df["upperband"], df["middleband"], df["lowerband"] = talib.BBANDS(
        close_prices,
        timeperiod=SCALPING_CONFIG["BBANDS_PERIOD"],
        nbdevup=SCALPING_CONFIG["BBANDS_STDDEV"],
        nbdevdn=SCALPING_CONFIG["BBANDS_STDDEV"],
    )

    for i in range(
        SCALPING_CONFIG["ATR_PERIOD"] + SCALPING_CONFIG["EMA_PERIOD"], len(df)
    ):  # Ajustar o início do loop para garantir dados suficientes para ATR e EMA
        window = df.iloc[
            :i
        ].copy()  # A janela agora contém todos os dados até o ponto atual, com indicadores pré-calculados

        # Certificar que a janela tem dados suficientes para os cálculos na lógica do agente
        if (
            len(window)
            < max(
                SCALPING_CONFIG["RSI_PERIOD"],
                SCALPING_CONFIG["EMA_PERIOD"],
                SCALPING_CONFIG["VOLUME_SMA_PERIOD"],
                SCALPING_CONFIG["MACD_SLOW"],
                SCALPING_CONFIG["ATR_PERIOD"],
                SCALPING_CONFIG["BBANDS_PERIOD"],
            )
            + 1
        ):
            continue

        current_price = df.iloc[i]["close"]
        current_time = df.index[i]

        # Passar a janela completa com indicadores para o agente
        # O ATR JÁ FOI CALCULADO no test_agent_scalping_offline.py
        # Apenas acedemos a ele aqui.
        if "atr" not in window.columns:
            print(
                "Erro: ATR não encontrado no DataFrame da janela. Por favor, calcule o ATR antes de chamar o agente."
            )
            continue  # Pula esta iteração se o ATR não estiver disponível

        result = agent_scalping_offline(
            "SUIUSDT", window, position
        )  # Passa a posição atual

        if not position and result["entry"]:
            # Calcular o tamanho da posição em dólares e a quantidade
            trade_value = equity * trade_percentage
            # Evitar divisões por zero ou trades minúsculos
            if trade_value < 0.001 or result["entry_price"] == 0:
                print(
                    f"Trade value muito pequeno ou preço zero: {trade_value:.4f}. Pulando entrada."
                )
                continue

            quantity = trade_value / result["entry_price"]

            # Usar a nova função para calcular TP/SL dinâmicos
            tp, sl = calculate_dynamic_tp_sl(
                result["entry_price"],
                window.iloc[-1]["atr"],  # Usar o ATR da janela atual
                window.iloc[-1]["rsi"],  # Usar o RSI da janela atual
                SCALPING_CONFIG.get(
                    "VOLATILITY_FACTOR", 1.0
                ),  # Adicionar um fator de volatilidade do config
            )
            position = {
                "entry_price": result["entry_price"],
                "tp": tp,
                "sl": sl,
                "trailing_stop_price": sl,  # Inicializa o trailing stop com o SL inicial
                "entry_time": current_time,
                "scale_count": 0,  # Inicializa o contador de escalonamento
                "quantity": quantity,  # Adicionar a quantidade
                "trade_value": trade_value,  # Valor em dólares do trade
            }
            print(
                f"ENTRADA em {current_time} | Preço: {result['entry_price']:.4f} | TP: {tp:.4f} | SL: {sl:.4f} | Qtd: {quantity:.4f}"
            )
            plot_trades_events.append(
                {"time": current_time, "price": result["entry_price"], "type": "entry"}
            )

        elif position:
            # Atualiza o preço do trailing stop
            # Ele deve apenas subir, nunca descer
            current_atr = window.iloc[-1]["atr"]
            new_trailing_stop = current_price - (
                current_atr * SCALPING_CONFIG["ATR_TRAILING_STOP_MULTIPLIER"]
            )
            position["trailing_stop_price"] = max(
                position["trailing_stop_price"], new_trailing_stop
            )
            plot_trailing_stop_events.append(
                {"time": current_time, "price": position["trailing_stop_price"]}
            )

            # Lógica de saída: TP/SL fixos ou sinais do agente
            if current_price >= position["tp"]:
                pnl = (position["tp"] - position["entry_price"]) * position["quantity"]
                trades.append(pnl)
                equity += pnl
                print(
                    f"SAÍDA por TP em {current_time} | Preço: {current_price:.4f} | PnL: {pnl:.4f}"
                )
                plot_trades_events.append(
                    {"time": current_time, "price": current_price, "type": "exit"}
                )
                position = None
            elif (
                current_price <= position["trailing_stop_price"]
            ):  # Usa o trailing stop para a saída
                pnl = (
                    position["trailing_stop_price"] - position["entry_price"]
                ) * position["quantity"]
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
                # Verifica a saída do agente
                agent_exit_signal, reason = result["exit"], result["reason"]
                if agent_exit_signal:
                    pnl = (current_price - position["entry_price"]) * position[
                        "quantity"
                    ]  # PnL ao preço atual
                    trades.append(pnl)
                    equity += pnl
                    print(
                        f"SAÍDA por {reason} em {current_time} | Preço: {current_price:.4f} | PnL: {pnl:.4f}"
                    )
                    plot_trades_events.append(
                        {"time": current_time, "price": current_price, "type": "exit"}
                    )
                    position = None

                # Lógica de escalonamento (pyramiding)
                # Esta lógica deve ser executada se não houver sinal de saída e ainda houver uma posição aberta
                if position:
                    can_scale, scale_size = should_scale_position(window, position)
                    if can_scale:
                        # Aqui você precisaria simular a adição de mais capital à posição
                        # Para este backtest offline, podemos apenas atualizar o entry_price médio
                        # e o TP/SL se for uma estratégia que recalcula.
                        # Por simplicidade, vamos apenas incrementar o scale_count para visualização.
                        position["scale_count"] += 1
                        print(
                            f"ESCALONAMENTO DE POSIÇÃO em {current_time} | Preço: {current_price:.4f} | Tamanho: {scale_size}"
                        )
                        # Se for para recalcular TP/SL após escalar, faça-o aqui:
                        # position["tp"], position["sl"] = calculate_dynamic_tp_sl(...)

    trades_df_for_plot = pd.DataFrame(plot_trades_events)
    trades_df_for_plot["time"] = pd.to_datetime(
        trades_df_for_plot["time"]
    )  # Converte o timestamp das trades para datetime
    trades_df_for_plot.set_index("time", inplace=True)

    trailing_stop_df = pd.DataFrame(plot_trailing_stop_events)
    if not trailing_stop_df.empty:
        trailing_stop_df["time"] = pd.to_datetime(trailing_stop_df["time"])
        trailing_stop_df.set_index("time", inplace=True)

    equity_curve = generate_equity_curve(initial_capital, trades)

    # Plotar os resultados no final
    plot_backtest_results(
        df, trades_df_for_plot, trailing_stop_df
    )  # Passa o DF completo com indicadores, o DF de trades e o DF do trailing stop

    return {
        "final_capital": equity,
        "profit": equity - initial_capital,
        "win_rate": win_rate(trades),
        "profit_factor": profit_factor(trades),
        "max_drawdown": max_drawdown(equity_curve),
        "avg_pnl": average_pnl(trades),
        "total_trades": len(trades),
    }


if __name__ == "__main__":
    results = run_backtest()
    print("\n===== Resultados do Backtest =====")
    for key, value in results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
