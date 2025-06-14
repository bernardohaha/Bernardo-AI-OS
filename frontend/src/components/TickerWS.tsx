import React, { useEffect, useState } from "react";

const TickerWS = ({ symbol = "SUI" }) => {
  const [price, setPrice] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}usdt@ticker`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setPrice(data.c);
    };
    return () => ws.close();
  }, [symbol]);

  return (
    <span className="ml-2 font-mono text-blue-800">
      {price ? `$${parseFloat(price).toFixed(4)}` : "..."}
    </span>
  );
};

export default TickerWS;
