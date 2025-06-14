import React from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"

import Dashboard from "./pages/Dashboard"
import Orders from "./pages/Orders"
import SymbolAnalysisPage from "./pages/SymbolAnalysisPage"
import PortfolioAnalysisPage from "./pages/PortfolioAnalysisPage"
import PositionAdvisorPage from "./pages/PositionAdvisorPage"
import SupervisorPage from "./pages/Supervisor"
import HistoricoDePosicoesPage from "./pages/HistoricoDePosicoesPage"
import PositionHistory from "./pages/PositionHistory";
import SymbolOverview from "./pages/SymbolOverview";



const AppRoutes = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/orders" element={<Orders />} />
      <Route path="/symbol" element={<SymbolAnalysisPage />} />
      <Route path="/portfolio" element={<PortfolioAnalysisPage />} />
      <Route path="/position-advisor" element={<PositionAdvisorPage />} />
      <Route path="/supervisor" element={<SupervisorPage />} />
      <Route path="/historico" element={<HistoricoDePosicoesPage />} />
      <Route path="/positions" element={<PositionHistory />} /> 
      <Route path="/moeda/:symbol" element={<SymbolOverview />} />
    </Routes>
  </BrowserRouter>
)

export default AppRoutes
