from backend.agents.agent_micro import agent_micro
from backend.agents.agent_meso import agent_meso
from backend.agents.agent_macro import agent_macro
from backend.services.orderbook_analysis_service import analyze_order_book
from backend.services.portfolio_memory_service import get_binance_position
from backend.services.trade_log_service import (
    log_analysis,
)  # novo ficheiro com função de logging


def supervisor_agent(symbol):
    symbol = symbol.upper()

    # Agentes especializados por timeframe
    micro = agent_micro(symbol)
    meso = agent_meso(symbol)
    macro = agent_macro(symbol)

    # Verificação de erros
    if "error" in micro or "error" in meso or "error" in macro:
        return {"symbol": symbol, "error": "Incomplete data from agents"}

    # Recomendações e confianças
    recs = [micro["recommendation"], meso["recommendation"], macro["recommendation"]]
    confidences = [micro["confidence"], meso["confidence"], macro["confidence"]]

    # Pesos de confiança por timeframe
    weights = {
        "micro": 0.4,
        "meso": 0.3,
        "macro": 0.3,
    }

    weighted_avg = round(
        micro["confidence"] * weights["micro"]
        + meso["confidence"] * weights["meso"]
        + macro["confidence"] * weights["macro"],
        2,
    )

    # Regras de consenso
    final_recommendation = "HOLD"
    if recs.count("BUY") >= 2:
        final_recommendation = "BUY"
    elif recs.count("SELL") >= 2:
        final_recommendation = "SELL"

    agreement_score = recs.count(final_recommendation)
    consensus_level = (
        "UNÂNIME"
        if agreement_score == 3
        else "MAIORIA"
        if agreement_score == 2
        else "DISCORDANTE"
    )

    # Serviços adicionais: Order Book + Posição Real
    orderbook = analyze_order_book(symbol)
    portfolio = get_binance_position(symbol)

    # Resultado final
    result = {
        "symbol": symbol,
        "final_recommendation": final_recommendation,
        "avg_confidence": weighted_avg,
        "consensus": consensus_level,
        "agents": {
            "micro": micro,
            "meso": meso,
            "macro": macro,
        },
        "orderbook": orderbook,
        "portfolio": portfolio,
    }

    # Log da análise para histórico
    log_analysis(symbol, result)

    return result
