import React, { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";

const HistoricoDePosicoesPage = () => {
  const [selectedSymbol1, setSelectedSymbol1] = useState("SUI");
  const [selectedSymbol2, setSelectedSymbol2] = useState("SOL");
  const [selectedSymbol3, setSelectedSymbol3] = useState("TAO");

  const [data1, setData1] = useState([]);
  const [data2, setData2] = useState([]);
  const [data3, setData3] = useState([]);

  const fetchTrades = async (symbol: string, setData: any) => {
  const res = await fetch(`http://localhost:8000/real_trades/${symbol}`);
  const json = await res.json();
  if (Array.isArray(json)) {
    setData(json);
  } else {
    setData([]); // fallback vazio para evitar crash
  }
};


  useEffect(() => {
    fetchTrades(selectedSymbol1, setData1);
    fetchTrades(selectedSymbol2, setData2);
    fetchTrades(selectedSymbol3, setData3);
  }, [selectedSymbol1, selectedSymbol2, selectedSymbol3]);

  const renderTable = (trades: any[]) => (
    <div className="bg-white rounded p-4 shadow max-h-[600px] overflow-y-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b font-bold">
            <th className="text-left">Entrada</th>
            <th className="text-left">Qtd</th>
            <th className="text-left">Lucro ($)</th>
            <th className="text-left">Lucro (%)</th>
            <th className="text-left">Sugestão</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t, i) => (
            <tr key={i} className="border-b">
              <td>${parseFloat(t.entry_price).toFixed(3)}</td>
              <td>{parseFloat(t.quantity).toFixed(2)}</td>
              <td className={t.profit_usd >= 0 ? "text-green-600" : "text-red-600"}>
                ${parseFloat(t.profit_usd).toFixed(2)}
              </td>
              <td className={t.profit_percent >= 0 ? "text-green-600" : "text-red-600"}>
                {parseFloat(t.profit_percent).toFixed(2)}%
              </td>
              <td>{t.suggestion}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const symbolOptions = ["SUI", "SOL", "TAO", "ALCH", "BTC", "ETH"];

  return (
    <MainLayout>
      <div className="p-6 space-y-6">
        <h2 className="text-3xl font-bold">Histórico de Posições</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[selectedSymbol1, selectedSymbol2, selectedSymbol3].map((symbol, i) => (
            <div key={i}>
              <select
                className="mb-2 w-full border p-2 rounded"
                value={symbol}
                onChange={(e) => {
                  const setter = [setSelectedSymbol1, setSelectedSymbol2, setSelectedSymbol3][i];
                  setter(e.target.value);
                }}
              >
                {symbolOptions.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              {renderTable([data1, data2, data3][i])}
            </div>
          ))}
        </div>
      </div>
    </MainLayout>
  );
};

export default HistoricoDePosicoesPage;
