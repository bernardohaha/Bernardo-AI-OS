# backend/backtesting/utils/metrics.py


def profit_factor(trades):
    total_gain = sum(t for t in trades if t > 0)
    total_loss = abs(sum(t for t in trades if t < 0))
    return round(total_gain / total_loss, 2) if total_loss > 0 else float("inf")


def win_rate(trades):
    wins = sum(1 for t in trades if t > 0)
    return round(100 * wins / len(trades), 2) if trades else 0


def average_pnl(trades):
    return round(sum(trades) / len(trades), 4) if trades else 0


def max_drawdown(equity_curve):
    peak = equity_curve[0]
    max_dd = 0
    for x in equity_curve:
        if x > peak:
            peak = x
        dd = peak - x
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


def generate_equity_curve(initial_capital, trades):
    equity = initial_capital
    curve = [equity]
    for t in trades:
        equity += t
        curve.append(equity)
    return curve
