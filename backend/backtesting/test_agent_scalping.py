# backend/backtesting/test_agent_scalping.py

import asyncio
from backend.agents.agent_scalping import agent_scalping
from backend.backtesting.data_loader import load_csv_candles


async def backtest_scalping(symbol="SUIUSDT", interval="1m", lookback=1000):
    candles = load_csv_candles(symbol, interval, folder="scalping", limit=lookback)
    trades = []
    capital = 1000.0
    base_capital = capital

    for i in range(60, len(candles) - 5):
        # Aqui, poderíamos montar candles fictícios se o scalping precisar de API
        result = await agent_scalping(
            symbol
        )  # ← adaptar se quiser simular sobre candles

        # Simula lógica baseada nos próximos candles (mock básico)
        next_close = float(candles[i + 3]["close"])  # Exemplo: 3 minutos depois
        # Aqui usarias a lógica interna do agent para decidir entry, sl, tp
        # Por agora deixamos fictício:
        trade_result = 0.3  # mock fixo
        trades.append(trade_result)
        capital += trade_result

    return {
        "final_capital": capital,
        "total_pnl": capital - base_capital,
        "trades": trades,
        "win_rate": round(100 * sum(t > 0 for t in trades) / len(trades), 2)
        if trades
        else 0,
        "num_trades": len(trades),
        "avg_pnl": round(sum(trades) / len(trades), 4) if trades else 0,
    }


if __name__ == "__main__":
    result = asyncio.run(backtest_scalping())
    for k, v in result.items():
        print(f"{k}: {v}")
