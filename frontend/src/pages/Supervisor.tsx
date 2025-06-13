import React, { useEffect, useState } from "react";
import SupervisorInsight from "../components/SupervisorInsight";
import CandleChart from "../components/CandleChart";
import MainLayout from "../layouts/MainLayout";


const SupervisorPage: React.FC = () => {
  const [symbol, setSymbol] = useState("SUI");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:8000/supervisor/${symbol}`)
      .then((res) => res.json())
      .then((result) => {
        setData(result);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Erro ao buscar dados:", err);
        setLoading(false);
      });
  }, [symbol]);

  return (
    <div className="p-6">
      <label className="block mb-2 font-medium">Escolhe um símbolo:</label>
      <select
        value={symbol}
        onChange={(e) => setSymbol(e.target.value)}
        className="mb-6 border p-2 rounded bg-white"
      >
        <option value="SUI">SUI</option>
        <option value="SOL">SOL</option>
        <option value="BTC">BTC</option>
        <option value="ETH">ETH</option>
        <option value="ALCH">ALCH</option>
        <option value="TAO">TAO</option>
      </select>

      {/* Gráfico + Orderbook lado a lado */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <CandleChart symbol={symbol} />
        {data?.orderbook && (
          <div className="bg-white p-4 rounded-xl shadow-md">
            <h2 className="text-lg font-semibold mb-2">📊 Order Book — Pressão de Mercado</h2>
            <p><strong>Pressão de Compra:</strong> ${data.orderbook.buy_pressure?.toLocaleString() || "N/A"}</p>
            <p><strong>Pressão de Venda:</strong> ${data.orderbook.sell_pressure?.toLocaleString() || "N/A"}</p>
            <p><strong>Ratio:</strong> {data.orderbook.pressure_ratio?.toFixed(2) || "N/A"}</p>
            <p>
              <strong>Sinal:</strong>{" "}
              <span className={
                data.orderbook.signal?.includes("compra")
                  ? "text-green-600 font-bold"
                  : data.orderbook.signal?.includes("venda")
                  ? "text-red-600 font-bold"
                  : "text-yellow-600 font-semibold"
              }>
                {data.orderbook.signal || "N/A"}
              </span>
            </p>
          </div>
        )}
      </div>

      {/* Dados Estratégicos */}
      {loading ? (
        <p>Carregando...</p>
      ) : data && !data.error ? (
        <SupervisorInsight data={data} />
      ) : (
        <p className="text-red-600">Erro ao carregar dados.</p>
      )}
    </div>
  );
};

export default () => (
  <MainLayout>
    <SupervisorPage />
  </MainLayout>
);