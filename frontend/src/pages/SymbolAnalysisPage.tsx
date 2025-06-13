import React, { useEffect, useState } from "react";
import SymbolCard from "../components/SymbolCard";
import MainLayout from "../layouts/MainLayout";


const SymbolAnalysisPage = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("http://localhost:8000/advisor/analyze/SUIUSDT")
      .then((res) => res.json())
      .then((json) => setData(json));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Análise de SUIUSDT</h1>
      {data ? (
        <SymbolCard
          data={data}
          onForceAction={() => alert(`Forçar execução para ${data.symbol}`)}
        />
      ) : (
        <p>A carregar...</p>
      )}
    </div>
  );
};

export default () => (
  <MainLayout>
    <SymbolAnalysisPage />
  </MainLayout>
);