from typing import Literal


def get_last_swing_high_low(
    highs: list[float],
    lows: list[float],
    lookback: int = 50,
    threshold_pct: float = 2.0,  # mínimo de oscilação entre high e low em percentagem
) -> dict[str, float | str]:
    """
    Identifica o último swing significativo nos dados.

    Args:
        highs: Lista de valores máximos das velas.
        lows: Lista de valores mínimos das velas.
        lookback: Nº de candles a considerar para o swing.
        threshold_pct: Oscilação mínima para considerar como swing, em percentagem.

    Returns:
        Dict com keys: 'high', 'low', 'direction'
    """
    highs = highs[-lookback:]
    lows = lows[-lookback:]

    high_idx = highs.index(max(highs))
    low_idx = lows.index(min(lows))

    high_val = highs[high_idx]
    low_val = lows[low_idx]
    diff_pct = abs(high_val - low_val) / max(high_val, low_val) * 100

    if diff_pct < threshold_pct:
        return {}  # Não há swing válido

    direction: Literal["uptrend", "downtrend"] = (
        "uptrend" if low_idx < high_idx else "downtrend"
    )

    return {
        "high": round(high_val, 4),
        "low": round(low_val, 4),
        "direction": direction,
    }
