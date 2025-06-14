import React, { useEffect, useState } from "react";
import CandleChart from "../components/CandleChart";
import OrderbookWS from "../components/OrderbookWS";
import TickerWS from "../components/TickerWS";
import MainLayout from "../layouts/MainLayout";

const SymbolOverview = () => {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("SUI");
  const [positions, setPositions] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [aiRecommendation, setAiRecommendation] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/portfolio")
      .then((res) => res.json())
      .then((data) => {
        const filtered = data.filter((item: any) => item.total > 0);
        const uniqueSymbols = filtered.map((item: any) => item.symbol.toUpperCase());
        setSymbols(uniqueSymbols);
        if (!uniqueSymbols.includes(selectedSymbol)) {
          setSelectedSymbol(uniqueSymbols[0]);
        }
      });
  }, []);

  useEffect(() => {
    fetch(`http://localhost:8000/portfolio_positions/${selectedSymbol}`)
      .then((res) => res.json())
      .then((data) => setPositions(data[selectedSymbol] || []));

    fetch("http://localhost:8000/real_orders")
      .then((res) => res.json())
      .then((data) => {
        const filtered = data.filter((o: any) => o.symbol === selectedSymbol);
        setOrders(filtered);
      });

    fetch(`http://localhost:8000/supervisor/${selectedSymbol}`)
      .then((res) => res.json())
      .then((data) => setAiRecommendation(data));
  }, [selectedSymbol]);

  return (
    <MainLayout>
      <div className="p-4 space-y-6">
        {/* Header com dropdown + preço + ícone */}
        <div className="flex items-center gap-4">
          <img
            src={`https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/${selectedSymbol.toLowerCase()}.png`}
            onError={(e) => (e.currentTarget.src = "/fallback-icon.png")}
            alt={selectedSymbol}
            width={32}
          />
          <h1 className="text-2xl font-bold">{selectedSymbol}</h1>
          <TickerWS symbol={selectedSymbol} />
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="ml-auto border px-2 py-1 rounded"
          >
            {symbols.map((sym) => (
              <option key={sym} value={sym}>
                {sym}
              </option>
            ))}
          </select>
        </div>

        {/* Gráfico + Orderbook lado a lado */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CandleChart symbol={selectedSymbol} />
          <OrderbookWS symbol={selectedSymbol} />
        </div>

        {/* Posições reais */}
        <div className="bg-white rounded p-4 shadow">
          <h2 className="text-lg font-semibold mb-2">📌 Posições Atuais</h2>
          {positions.length > 0 ? (
            <ul className="text-sm">
              {positions.map((p, i) => (
                <li key={i}>
                  ✅ {p.quantity} @ ${p.entry_price} — PNL: {p.pnl_usd.toFixed(2)} USD / {p.pnl_percent.toFixed(2)}%
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">Nenhuma posição ativa.</p>
          )}
        </div>

        {/* Ordens de venda ativas */}
        <div className="bg-white rounded p-4 shadow">
          <h2 className="text-lg font-semibold mb-2">📤 Ordens de Venda Ativas</h2>
          {orders.length > 0 ? (
            <ul className="text-sm">
              {orders.map((o, i) => (
                <li key={i}>
                  📍 {o.side} {o.quantity} @ ${o.price}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">Nenhuma ordem ativa encontrada.</p>
          )}
        </div>

        {/* Recomendação AI */}
        <div className="bg-white rounded p-4 shadow">
          <h2 className="text-lg font-semibold mb-2">🤖 Recomendação AI</h2>
          {aiRecommendation ? (
            <div className="text-sm">
              <p>🔹 Micro: {aiRecommendation.micro_recommendation}</p>
              <p>🔸 Meso: {aiRecommendation.meso_recommendation}</p>
              <p>🔺 Macro: {aiRecommendation.macro_recommendation}</p>
              <p className="mt-2 font-bold">
                ✅ Supervisor: {aiRecommendation.supervisor_recommendation} — força: {aiRecommendation.strength}/10
              </p>
              <p className="mt-1 text-sm">Zona de Compra: ${aiRecommendation.buy_zone} | Zona de Venda: ${aiRecommendation.sell_zone}</p>
            </div>
          ) : (
            <p className="text-gray-500">Sem recomendação disponível.</p>
          )}
        </div>
      </div>
    </MainLayout>
  );
};

export default SymbolOverview;
