import React, { useEffect, useState } from 'react';

interface Order {
  id: number;
  symbol: string;
  type: string;
  side: string;
  price: number;
  quantity: number;
  status: string;
}

const OrdersTable: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/orders")
      .then((res) => res.json())
      .then((data) => {
        // Como o backend não tem IDs, vamos gerar index temporário
        const dataWithIds = data.map((order: any, idx: number) => ({
          id: idx + 1,
          symbol: order.symbol,
          type: order.type,
          side: order.side,
          price: order.price,
          quantity: order.quantity,
          status: order.status,
        }));
        setOrders(dataWithIds);
      });
  }, []);

  return (
    <div className="bg-white shadow rounded p-4">
      <table className="min-w-full">
        <thead>
          <tr>
            <th className="text-left py-2 px-4">ID</th>
            <th className="text-left py-2 px-4">Par</th>
            <th className="text-left py-2 px-4">Tipo</th>
            <th className="text-left py-2 px-4">Lado</th>
            <th className="text-left py-2 px-4">Preço</th>
            <th className="text-left py-2 px-4">Quantidade</th>
            <th className="text-left py-2 px-4">Estado</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id}>
              <td className="py-2 px-4">{order.id}</td>
              <td className="py-2 px-4">{order.symbol}</td>
              <td className="py-2 px-4">{order.type}</td>
              <td className="py-2 px-4">{order.side}</td>
              <td className="py-2 px-4">{order.price}</td>
              <td className="py-2 px-4">{order.quantity}</td>
              <td className="py-2 px-4">{order.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default OrdersTable;
