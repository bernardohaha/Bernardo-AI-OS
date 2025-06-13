import React from "react";
import { Link } from "react-router-dom";

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-[#7b5e3e] text-white p-6 space-y-6">
        <h2 className="text-2xl font-bold">🧠 AI Trading</h2>
        <nav className="space-y-2">
          <Link to="/" className="block hover:text-yellow-400">Dashboard</Link>
          <Link to="/supervisor" className="block hover:text-yellow-400">Supervisor</Link>
          <Link to="/advisor" className="block hover:text-yellow-400">Position Advisor</Link>
          <Link to="/portfolio" className="block hover:text-yellow-400">Portfolio</Link>
          <Link to="/orders" className="block hover:text-yellow-400">Ordens</Link>
          <Link to="/historico" className="block hover:text-yellow-400">Histórico</Link>
          <Link to="/positions" className="block hover:text-yellow-400">Minhas Posições</Link>
        </nav>
      </aside>

      {/* Conteúdo principal */}
      <main className="flex-1 bg-gray-50 p-6 overflow-auto">
        {children}
      </main>
    </div>
  );
};

export default MainLayout;
