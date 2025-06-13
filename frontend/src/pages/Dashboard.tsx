import React from 'react';
import PortfolioTable from '../components/PortfolioTable';
import MainLayout from "../layouts/MainLayout";


const DashboardPage = () => {
  return (
    <div className="p-10">
      <h1 className="text-3xl font-bold mb-6">Bernardo AI OS</h1>
      <p className="mb-6">
        O teu centro de gestão de Trading e Portfolio está a nascer 🚀
      </p>
      <PortfolioTable />
    </div>
  );
};

export default () => (
  <MainLayout>
    <DashboardPage />
  </MainLayout>
);