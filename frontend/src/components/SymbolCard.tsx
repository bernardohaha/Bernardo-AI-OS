import React from "react";

type SymbolAnalysis = {
  symbol: string;
  RSI: number;
  EMA9: number;
  EMA21: number;
  recommendation: string;
  orderbook_pressure: string;
  strength: string;
};

type Props = {
  data: SymbolAnalysis;
  onForceAction?: () => void;
};

const getColor = (recommendation: string, strength: string) => {
  if (strength === "STRONG BUY") return "bg-green-600 text-white";
  if (strength === "STRONG SELL") return "bg-red-600 text-white";
  if (recommendation.includes("HOLD")) return "bg-gray-300 text-gray-800";
  if (recommendation.includes("BUY")) return "bg-green-200 text-green-800";
  if (recommendation.includes("SELL")) return "bg-red-200 text-red-800";
  return "bg-white";
};

const SymbolCard: React.FC<Props> = ({ data, onForceAction }) => {
  const color = getColor(data.recommendation, data.strength);

  return (
    <div className={`rounded-xl shadow-md p-4 m-2 ${color}`}>
      <div className="text-xl font-semibold">{data.symbol}</div>
      <div className="text-sm mt-1">
        <div>RSI: {data.RSI ?? data.rsi ?? "N/A"}</div>
        <div>EMA9: {data.EMA9 ?? data.ema_fast ?? "N/A"}</div>
        <div>EMA21: {data.EMA21 ?? data.ema_slow ?? "N/A"}</div>
        <div>Pressão: <span className="font-bold">{data.orderbook_pressure}</span></div>
        <div>Força: <span className="font-bold">{data.strength}</span></div>
      </div>

      <div className="mt-3 font-medium">Recomendação: {data.recommendation}</div>

      {onForceAction && (
        <button
          onClick={onForceAction}
          className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Forçar Ação Manual
        </button>
      )}
    </div>
  );
};

export default SymbolCard;
