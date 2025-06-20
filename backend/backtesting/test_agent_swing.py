# backend/backtesting/test_agent_swing.py

from backend.agents.agent_swing import analyze_swing
from backend.backtesting.data_loader import load_csv_candles


def backtest_swing(symbol="SUIUSDT", interval="1h", lookback=200):
    candles = load_csv_candles(symbol, interval, folder="swing", limit=lookback)
    trades = []
    capital = 1000.0
    base_capital = capital

    for i in range(60, len(candles) - 10):
        sub_candles = candles[i - 60 : i]
        result = analyze_swing(symbol, sub_candles)

        if result["recommendation"] == "BUY":
            entry = result["entries"][0]
            tp = result["take_profits"][0]
            sl = result["stop_loss"]
            next_price = float(
                candles[i + 5]["close"]
            )  # 5 candles depois (simula trade curto)

            if next_price >= tp:
                pnl = tp - entry
                trades.append(pnl)
                capital += pnl
            elif next_price <= sl:
                pnl = sl - entry
                trades.append(pnl)
                capital += pnl
            else:
                trades.append(0)

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
    result = backtest_swing()
    for k, v in result.items():
        print(f"{k}: {v}")
