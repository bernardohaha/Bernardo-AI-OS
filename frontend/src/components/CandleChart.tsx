import React, { useEffect, useRef, useState } from "react";
import { createChart } from "lightweight-charts";

const intervals = ["1m", "5m", "15m", "1h", "4h", "1d"];

const CandleChart = ({ symbol }: { symbol: string }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const candleSeriesRef = useRef<any>(null);
  const [interval, setInterval] = useState("1m");

  useEffect(() => {
    if (!chartRef.current) return;

    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 300,
      layout: { textColor: "#000", background: { color: "#f9f9f9" } },
      grid: { vertLines: { color: "#eee" }, horzLines: { color: "#eee" } },
      timeScale: { timeVisible: true, secondsVisible: false },
      crosshair: { mode: 1 },
    });

    const candleSeries = chart.addCandlestickSeries();
    candleSeriesRef.current = candleSeries;

    function toCandle(candle: any) {
      return {
        time: Math.floor(candle.t / 1000),
        open: parseFloat(candle.o),
        high: parseFloat(candle.h),
        low: parseFloat(candle.l),
        close: parseFloat(candle.c),
      };
    }

    let ws: WebSocket;

    const fetchAndSubscribe = async () => {
      // REST (inicial)
      const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${symbol}USDT&interval=${interval}&limit=100`);
      const data = await res.json();
      const candles = data.map((k: any) => ({
        time: k[0] / 1000,
        open: parseFloat(k[1]),
        high: parseFloat(k[2]),
        low: parseFloat(k[3]),
        close: parseFloat(k[4]),
      }));
      candleSeries.setData(candles);

      // WebSocket (ao vivo)
      ws = new WebSocket(`wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}usdt@kline_${interval}`);
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.k && msg.k.x) {
          const newCandle = toCandle(msg.k);
          candleSeries.update(newCandle);
        }
      };
    };

    fetchAndSubscribe();

    const resize = () => {
      chart.applyOptions({ width: chartRef.current!.clientWidth });
    };

    window.addEventListener("resize", resize);
    return () => {
      chart.remove();
      ws?.close();
      window.removeEventListener("resize", resize);
    };
  }, [symbol, interval]);

  return (
    <div className="bg-white p-4 rounded-xl shadow h-full">
      <div className="flex justify-between mb-2">
        <h2 className="text-lg font-semibold">📊 Gráfico de Velas ({symbol})</h2>
        <select
          value={interval}
          onChange={(e) => setInterval(e.target.value)}
          className="border px-2 py-1 rounded"
        >
          {intervals.map((intv) => (
            <option key={intv} value={intv}>{intv}</option>
          ))}
        </select>
      </div>
      <div ref={chartRef} className="w-full" />
    </div>
  );
};

export default CandleChart;
