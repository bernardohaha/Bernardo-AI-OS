import numpy as np
from scipy.stats import gaussian_kde


def detect_price_zones(
    closes, highs=None, lows=None, volumes=None, num_zones=2, bandwidth=0.01
):
    prices = np.array(closes)
    if len(prices) < 20:
        return []

    price_range = np.linspace(prices.min(), prices.max(), 200)

    try:
        kde = gaussian_kde(prices, bw_method=bandwidth)
        density = kde(price_range)

        # Verifica se existe densidade válida
        if not np.any(density > 0):
            raise ValueError("Densidade KDE vazia")

        peaks_idx = np.argsort(density)[-num_zones:]
        peaks = sorted(price_range[peaks_idx])

        zones = [(round(p * 0.985, 4), round(p * 1.015, 4)) for p in peaks]
        return zones

    except Exception as e:
        print(f"[ERRO KDE] Fallback para histograma: {e}")

        try:
            counts, bin_edges = np.histogram(prices, bins=20)
            top_bins = np.argsort(counts)[-num_zones:]
            zones = []

            for idx in sorted(top_bins):
                low = bin_edges[idx]
                high = bin_edges[idx + 1]
                zones.append((round(low, 4), round(high, 4)))

            return zones

        except Exception as fallback_error:
            print(f"[ERRO HISTOGRAMA] {fallback_error}")
            return []


def calculate_fibonacci_zones(closes):
    high = max(closes)
    low = min(closes)
    diff = high - low

    fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
    zones = []

    for level in fib_levels:
        price = high - (diff * level)
        margin = price * 0.01  # margem de 1%
        zones.append((round(price - margin, 4), round(price + margin, 4)))

    return zones
