import React, { useEffect, useState } from 'react';
import axios from 'axios';
import MainLayout from "../layouts/MainLayout";


const getSuggestionStyle = (suggestion: string) => {
  if (suggestion.includes("BUY") && !suggestion.includes("bloqueado")) {
    return { color: "green", icon: "🟢" };
  }
  if (suggestion.includes("SELL") && !suggestion.includes("bloqueado")) {
    return { color: "red", icon: "🔴" };
  }
  if (suggestion.includes("bloqueado")) {
    return { color: "orange", icon: "🟠" };
  }
  return { color: "gray", icon: "⚪" };
};

const PositionCard = ({ symbol, suggestion, buyZone, sellZone, confidence, expectedProfit }) => {
  const { color, icon } = getSuggestionStyle(suggestion);

  return (
    <div className="bg-gray-100 p-4 rounded-xl shadow-md w-full max-w-md">
      <h2 className="text-xl font-semibold mb-2">{symbol}</h2>
      <p>⬆️ <span className="font-medium">Zona de Venda:</span> ${sellZone?.min ?? '-'} a ${sellZone?.max ?? '-'}</p>
      <p>🔽 <span className="font-medium">Zona de Compra:</span> ${buyZone?.min ?? '-'} a ${buyZone?.max ?? '-'}</p>
      <p>🎯 <span className="font-medium">Confiança:</span> {confidence != null ? `${(confidence * 100).toFixed(1)}%` : '-'}</p>
      <p>💸 <span className="font-medium">Lucro Potencial:</span> {expectedProfit != null ? `${expectedProfit.toFixed(2)}%` : '-'}</p>
      <p className="mt-2" style={{ color }}>
        {icon} <span className="font-medium">Sugestão:</span> {suggestion}
      </p>
    </div>
  );
};

const PositionAdvisorPage = () => {
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:8000/advisor/analyze-portfolio').then(res => {
      setRecommendations(res.data);
    });
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Sugestões de Entrada e Saída</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {recommendations.map((rec, index) => (
          <PositionCard
            key={index}
            symbol={rec.symbol}
            suggestion={rec.recommendation}
            buyZone={rec.buy_zone || { min: "-", max: "-" }}
            sellZone={rec.sell_zone || { min: "-", max: "-" }}
            confidence={rec.confidence}
            expectedProfit={rec.expected_profit_pct}
          />
        ))}
      </div>
    </div>
  );
};

export default () => (
  <MainLayout>
    <PositionAdvisorPage />
  </MainLayout>
);