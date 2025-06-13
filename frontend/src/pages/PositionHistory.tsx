import React, { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";

interface Macro {
  total_investido: number;
  preco_medio: number;
  quantidade_total: number;
  pnl_atual: number;
  pnl_percent: number;
}

interface Micro {
  side: string;
  quantity: number;
  price: number;
  value: number;
  timestamp: number;
  status: string;
}

interface Positions {
  [symbol: string]: {
    macro: Macro;
    micro: Micro[];
    recomendacao: string;
  };
}

const PositionHistory = () => {
  const [positions, setPositions] = useState<Positions>({});
  const [selectedSymbol, setSelectedSymbol] = useState<string>("SUI");

  useEffect(() => {
    fetch("http://localhost:8000/positions")
      .then((res) => res.json())
      .then((data) => setPositions(data));
  }, []);

  const symbols = Object.keys(positions);

  if (symbols.length === 0) {
    return (
      <MainLayout>
        <div>A carregar posições...</div>
      </MainLayout>
    );
  }

  // Atualiza o símbolo selecionado caso desapareça do estado
  useEffect(() => {
    if (symbols.length && !symbols.includes(selectedSymbol)) {
      setSelectedSymbol(symbols[0]);
    }
  }, [symbols, selectedSymbol]);

  const macro = positions[selectedSymbol]?.macro;
  const micro = positions[selectedSymbol]?.micro || [];
  const recomendacao = positions[selectedSymbol]?.recomendacao;

  return (
    <MainLayout>
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-4 flex items-center gap-2">
          <img
            src={`https://coinicons-api.vercel.app/api/icon/${selectedSymbol.toLowerCase()}`}
            alt={selectedSymbol}
            width={32}
            style={{ display: "inline" }}
          />
          {selectedSymbol} — Minhas Posições
        </h1>
        <select
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="mb-6 p-2 border rounded bg-white"
        >
          {symbols.map((symbol) => (
            <option key={symbol} value={symbol}>
              {symbol}
            </option>
          ))}
        </select>

        {macro && (
          <div className="mb-4 bg-gray-100 p-4 rounded flex flex-col md:flex-row items-center gap-8">
            <img
              src={`https://coinicons-api.vercel.app/api/icon/${selectedSymbol.toLowerCase()}`}
              alt={selectedSymbol}
              width={48}
              className="mr-2"
            />
            <div>
              <div><b>Total Investido:</b> ${macro.total_investido}</div>
              <div><b>Preço Médio:</b> ${macro.preco_medio}</div>
              <div><b>Quantidade:</b> {macro.quantidade_total}</div>
              <div>
                <b>PNL:</b>{" "}
                <span className={macro.pnl_atual >= 0 ? "text-green-600 font-semibold" : "text-red-600 font-semibold"}>
                  ${macro.pnl_atual} ({macro.pnl_percent}%)
                </span>
              </div>
              <div>
                <b>Recomendação AI:</b>{" "}
                <span className="font-semibold">{recomendacao}</span>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded p-4 shadow max-h-[600px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b font-bold">
                <th>Side</th>
                <th>Qtd</th>
                <th>Preço</th>
                <th>Valor</th>
                <th>Status</th>
                <th>Data/Hora</th>
              </tr>
            </thead>
            <tbody>
              {micro.map((pos, i) => (
                <tr key={i} className={pos.status === "fechada" ? "bg-gray-100" : ""}>
                  <td>{pos.side}</td>
                  <td>{pos.quantity}</td>
                  <td>${pos.price}</td>
                  <td>${pos.value.toFixed(2)}</td>
                  <td>
                    <span className={pos.status === "aberta" ? "text-yellow-700 font-bold" : "text-gray-600"}>
                      {pos.status}
                    </span>
                  </td>
                  <td>{new Date(pos.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {micro.length === 0 && (
            <div className="text-gray-400 mt-6 text-center">Sem posições encontradas para {selectedSymbol}.</div>
          )}
        </div>
      </div>
    </MainLayout>
  );
};

export default PositionHistory;
