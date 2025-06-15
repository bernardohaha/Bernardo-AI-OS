from typing import Dict


def evaluate_fibonacci_impact(
    current_price: float, fib_data: Dict, threshold_pct: float = 0.5
) -> Dict:
    """
    Avalia o impacto dos níveis de Fibonacci no preço atual e retorna uma sugestão de bias.

    Returns:
        {
            "bias": "bullish" | "bearish" | "neutral",
            "reason": "Texto explicativo"
        }
    """
    direction = fib_data.get("direction")
    retracements = fib_data.get("retracements", {})

    # Prioridade explícita dos níveis
    priority = ["0.618", "0.5", "0.382", "0.236", "0.786"]

    for label in priority:
        if label in retracements:
            level = retracements[label]
            proximity_pct = abs(current_price - level) / current_price * 100
            if proximity_pct <= threshold_pct:
                if direction == "uptrend" and current_price > level:
                    return {
                        "bias": "bullish",
                        "reason": f"Fibonacci {label} atuando como suporte",
                    }
                elif direction == "downtrend" and current_price < level:
                    return {
                        "bias": "bearish",
                        "reason": f"Fibonacci {label} atuando como resistência",
                    }

    return {"bias": "neutral", "reason": "Nenhum nível de Fibonacci com impacto direto"}
