import React from "react";

interface AgentResult {
  recommendation: string;
  confidence: number;
  strength: string;
  expected_profit_pct?: number;
  buy_zone: { min: number | null; max: number | null };
  sell_zone: { min: number | null; max: number | null };
  pattern_implication?: string;
  pattern_strength?: string;
  detected_patterns?: { pattern: string; type: string; strength: number }[];
}

interface OrderbookData {
  buy_pressure: number;
  sell_pressure: number;
  pressure_ratio: number;
  signal: string;
}

interface SupervisorProps {
  symbol: string;
  recommendation: string;
  avg_confidence: number;
  consensus: string;
  agents: {
    micro: AgentResult;
    meso: AgentResult;
    macro: AgentResult;
  };
  orderbook?: OrderbookData;
}

const formatZone = (zone: { min: number | null | undefined; max: number | null | undefined }) => {
  const minFormatted = zone?.min != null ? zone.min.toFixed(3) : null;
  const maxFormatted = zone?.max != null ? zone.max.toFixed(3) : null;
  if (minFormatted && maxFormatted) {
    return `$${minFormatted} - $${maxFormatted}`;
  }
  return "N/A";
};

const formatConfidence = (val: number) => `${Math.round(val * 100)}%`;

const SupervisorInsight: React.FC<{ data: SupervisorProps }> = ({ data }) => {
  const icons = { micro: "📊", meso: "📈", macro: "🌐" };
  const label = { micro: "Agente Micro", meso: "Agente Meso", macro: "Agente Macro" };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Bloco principal */}
      <div className="bg-white p-4 rounded-xl shadow-md mb-6">
        <h1 className="text-2xl font-bold mb-2">Resumo Estratégico: {data.symbol}</h1>
        <p className="text-lg">🧠 <strong>Recomendação Final:</strong> {data.recommendation}</p>
        <p>📊 Confiança Média: {formatConfidence(data.avg_confidence)}</p>
        <p>🤝 Consenso: <strong>{data.consensus}</strong></p>
      </div>

      {/* Bloco dos Agentes */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(data.agents).map(([key, agent]) => (
          <div key={key} className="bg-white p-4 rounded-xl shadow-md">
            <h2 className="text-lg font-semibold mb-2">
              {icons[key as keyof typeof icons]} {label[key as keyof typeof label]}
            </h2>
            <p>🎯 <strong>{agent.recommendation}</strong> ({agent.strength})</p>
            <p>📑 Confiança: {formatConfidence(agent.confidence)}</p>
            <p>💰 Lucro Potencial: {agent.expected_profit_pct != null ? `${agent.expected_profit_pct.toFixed(2)}%` : "-"}</p>
            <p>🔻 Zona de Compra: {formatZone(agent.buy_zone)}</p>
            <p>🔺 Zona de Venda: {formatZone(agent.sell_zone)}</p>

            {/* Destaque dos padrões */}
            {agent.pattern_implication && (
              <p>
                🧠 Padrões:{" "}
                <span className={
                  agent.pattern_implication === "BULLISH"
                    ? "text-green-600 font-semibold"
                    : agent.pattern_implication === "BEARISH"
                    ? "text-red-600 font-semibold"
                    : "text-yellow-600"
                }>
                  {agent.pattern_implication} ({agent.pattern_strength})
                </span>
              </p>
            )}

            {agent.detected_patterns && agent.detected_patterns.length > 0 && (
              <ul className="text-sm text-gray-600 mt-1 list-disc ml-4">
                {agent.detected_patterns.map((p, i) => (
                  <li key={i}>
                    {p.pattern} ({p.type}, força: {p.strength})
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SupervisorInsight;
