from typing import Dict, Literal
from backend.services.swing_detection_service import get_last_swing_high_low


def calculate_fibonacci_levels_from_swing(
    high: float, low: float, direction: Literal["uptrend", "downtrend"]
) -> Dict[str, float]:
    """
    Calcula os níveis de retração de Fibonacci (0.236 a 0.786) com base num swing específico.
    """
    diff = high - low
    levels = {}

    if direction == "uptrend":
        levels = {
            "0.236": round(high - 0.236 * diff, 4),
            "0.382": round(high - 0.382 * diff, 4),
            "0.5": round(high - 0.5 * diff, 4),
            "0.618": round(high - 0.618 * diff, 4),
            "0.786": round(high - 0.786 * diff, 4),
        }
    else:  # downtrend
        levels = {
            "0.236": round(low + 0.236 * abs(diff), 4),
            "0.382": round(low + 0.382 * abs(diff), 4),
            "0.5": round(low + 0.5 * abs(diff), 4),
            "0.618": round(low + 0.618 * abs(diff), 4),
            "0.786": round(low + 0.786 * abs(diff), 4),
        }

    return levels


def calculate_fibonacci_extensions_from_swing(
    high: float, low: float, direction: Literal["uptrend", "downtrend"]
) -> Dict[str, float]:
    """
    Calcula níveis de extensão de Fibonacci (objetivos de preço).
    """
    diff = high - low
    extensions = {}

    if direction == "uptrend":
        extensions = {
            "1.272": round(high + 0.272 * diff, 4),
            "1.618": round(high + 0.618 * diff, 4),
            "2.0": round(high + 1.0 * diff, 4),
            "2.618": round(high + 1.618 * diff, 4),
        }
    else:
        extensions = {
            "1.272": round(low - 0.272 * abs(diff), 4),
            "1.618": round(low - 0.618 * abs(diff), 4),
            "2.0": round(low - 1.0 * abs(diff), 4),
            "2.618": round(low - 1.618 * abs(diff), 4),
        }

    return extensions


def get_fibonacci_data_from_price_series(
    highs: list[float],
    lows: list[float],
    lookback: int = 50,
    threshold_pct: float = 2.0,
) -> Dict[str, Dict[str, float] | str]:
    """
    Integra swing detection + Fibonacci. Ideal para o agente usar diretamente.

    Returns:
        {
            "direction": "uptrend",
            "retracements": {...},
            "extensions": {...}
        }
        ou {} se não houver swing válido
    """
    swing = get_last_swing_high_low(highs, lows, lookback, threshold_pct)
    if not swing:
        return {}

    retracements = calculate_fibonacci_levels_from_swing(
        swing["high"], swing["low"], swing["direction"]
    )
    extensions = calculate_fibonacci_extensions_from_swing(
        swing["high"], swing["low"], swing["direction"]
    )

    return {
        "direction": swing["direction"],
        "retracements": retracements,
        "extensions": extensions,
    }
