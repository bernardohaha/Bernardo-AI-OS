from typing import Literal, Dict, List
import numpy as np


def detect_rsi_divergence(
    closes: List[float], rsis: List[float], lookback: int = 20
) -> Dict[str, str | int]:
    """
    Detecta divergências bullish ou bearish entre o preço (closes) e o RSI.
    Melhorado para procurar divergências entre pontos de "swing" simples (comparando com i-2)
    e priorizar a divergência mais recente.

    Retorna:
        {
            "type": "bullish" | "bearish" | "none",
            "index": int  # onde foi detetada a divergência
        }
    """
    if len(closes) < lookback or len(rsis) < lookback:
        return {"type": "none", "index": -1}

    # Inverte a ordem do loop para procurar a divergência mais recente primeiro
    # Começa em -2 para ter acesso a [i-2]
    # Vai até -lookback - 1 (para incluir -lookback)
    for i in range(-2, -lookback - 1, -1):
        # Para que 'i-2' seja válido, precisamos de pelo menos 3 candles
        if abs(i) + 2 > len(closes):  # Garante que closes[i-2] existe
            continue

        # === DIVERGÊNCIA BULLISH (Preço faz Mínimo Mais Baixo, RSI faz Mínimo Mais Alto) ===
        # Procura um fundo no preço (closes[i] é menor que closes[i-1] e closes[i-2])
        # E um fundo no RSI (rsis[i] é maior que rsis[i-1] e rsis[i-2])
        # Simplificação: Preço (closes[i] < closes[i-2]) E RSI (rsis[i] > rsis[i-2])
        if closes[i] < closes[i - 2] and rsis[i] > rsis[i - 2]:
            # Validação extra: garantir que não é apenas um ruído,
            # e que o ponto i-1 está entre os pontos (i-2 e i)
            # ou que pelo menos a tendência do RSI/Preço se inverteu
            if (
                closes[i - 1] >= closes[i] and rsis[i - 1] <= rsis[i]
            ):  # Garante que o RSI não está a cair tão agressivamente quanto o preço
                return {"type": "bullish", "index": len(closes) + i}

        # === DIVERGÊNCIA BEARISH (Preço faz Máximo Mais Alto, RSI faz Máximo Mais Baixo) ===
        # Procura um topo no preço (closes[i] é maior que closes[i-1] e closes[i-2])
        # E um topo no RSI (rsis[i] é menor que rsis[i-1] e rsis[i-2])
        # Simplificação: Preço (closes[i] > closes[i-2]) E RSI (rsis[i] < rsis[i-2])
        elif closes[i] > closes[i - 2] and rsis[i] < rsis[i - 2]:
            # Validação extra: garantir que não é apenas um ruído
            if (
                closes[i - 1] <= closes[i] and rsis[i - 1] >= rsis[i]
            ):  # Garante que o RSI não está a subir tão agressivamente quanto o preço
                return {"type": "bearish", "index": len(closes) + i}

    return {"type": "none", "index": -1}
