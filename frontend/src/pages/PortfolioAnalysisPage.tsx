import React, { useEffect, useState } from "react";
import SymbolCard from "../components/SymbolCard";
import PortfolioTable from "../components/PortfolioTable";
import MainLayout from "../layouts/MainLayout";

const PortfolioAnalysisPage = () => {
  const [portfolio, setPortfolio] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/advisor/analyze-portfolio")
      .then((res) => res.json())
      .then((json) => setPortfolio(json));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Análise do Portfólio</h1>

      {/* Cartões com sugestões específicas por ativo */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {portfolio.map((item: any) => (
          <SymbolCard
            key={item.symbol}
            data={item}
            onForceAction={() =>
              alert(`Forçar ação manual para ${item.symbol}`)
            }
          />
        ))}
      </div>

      {/* Tabela completa com todas as posições */}
      <PortfolioTable />
    </div>
  );
};

export default () => (
  <MainLayout>
    <PortfolioAnalysisPage />
  </MainLayout>
);
