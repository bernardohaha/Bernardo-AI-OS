import React, { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";

interface Order {
  symbol: string;
  side: string;
  type: string;
  price: string;
  origQty: string;
  status: string;
  time: number;
}

const Orders = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/real_orders")
      .then((res) => res.json())
      .then((json) => {
        setOrders(json);
        setLoading(false);
      });
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">📋 Ordens Ativas na Binance</h1>
      {loading ? (
        <p>A carregar ordens reais...</p>
      ) : orders.length === 0 ? (
        <p>Nenhuma ordem ativa neste momento.</p>
      ) : (
        <table className="w-full text-sm border">
          <thead className="bg-gray-100">
            <tr>
              <th>Símbolo</th>
              <th>Lado</th>
              <th>Tipo</th>
              <th>Preço</th>
              <th>Qtd</th>
              <th>Valor (USD)</th>
              <th>Status</th>
              <th>Hora</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order, i) => {
              const price = parseFloat(order.price);
              const quantity = parseFloat(order.origQty);
              const totalValue = price * quantity;
              const isBuy = order.side === "BUY";

              return (
                <tr key={i} className="text-center border-t">
                  <td>{order.symbol}</td>
                  <td className={isBuy ? "text-green-600 font-semibold" : "text-red-600 font-semibold"}>
                    {order.side}
                  </td>
                  <td>{order.type}</td>
                  <td>${price.toFixed(4)}</td>
                  <td>{quantity.toFixed(2)}</td>
                  <td className={isBuy ? "text-green-600" : "text-red-600"}>
                    ${totalValue.toFixed(2)}
                  </td>
                  <td>{order.status}</td>
                  <td>{new Date(order.time).toLocaleString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default () => (
  <MainLayout>
    <Orders />
  </MainLayout>
);
