import React, { useEffect, useState } from "react";

const OrderbookWS = ({ symbol = "SUI" }) => {
  const [bids, setBids] = useState([]);
  const [asks, setAsks] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(`wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}usdt@depth20@100ms`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setBids(data.bids.slice(0, 10));
      setAsks(data.asks.slice(0, 10));
    };
    return () => ws.close();
  }, [symbol]);

  return (
    <div className="bg-white rounded p-4 shadow">
      <h2 className="font-bold text-lg mb-2">📒 Order Book ({symbol})</h2>
      <div className="flex gap-4">
        <div className="flex-1">
          <div className="font-semibold mb-1 text-green-700">Bids</div>
          <table className="w-full text-xs">
            <tbody>
              {bids.map(([price, qty], i) => (
                <tr key={i}>
                  <td className="text-green-700">${parseFloat(price).toFixed(4)}</td>
                  <td>{parseFloat(qty).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex-1">
          <div className="font-semibold mb-1 text-red-700">Asks</div>
          <table className="w-full text-xs">
            <tbody>
              {asks.map(([price, qty], i) => (
                <tr key={i}>
                  <td className="text-red-700">${parseFloat(price).toFixed(4)}</td>
                  <td>{parseFloat(qty).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default OrderbookWS;
