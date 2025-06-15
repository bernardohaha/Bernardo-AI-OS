import numpy as np
from typing import List


def calculate_volume_ema(volumes: List[float], period: int = 20) -> float:
    """
    Calcula a média móvel exponencial (EMA) do volume.
    """
    if len(volumes) < period:
        return np.mean(volumes)

    weights = np.exp(np.linspace(-1.0, 0.0, period))
    weights /= weights.sum()
    ema = np.convolve(volumes[-period:], weights, mode="valid")[0]
    return ema


def is_volume_spike(
    current_volume: float, vma_volume: float, multiplier: float = 1.5
) -> bool:
    """
    Verifica se o volume atual é significativamente maior que a média (spike).
    """
    return current_volume > multiplier * vma_volume
