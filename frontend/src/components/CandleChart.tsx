import React, { useEffect, useRef } from "react";
import { createChart } from "lightweight-charts";

const CandleChart = ({ symbol }: { symbol: string }) => {
  const chartRef = useRef<HTMLDivElement>(null);

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

    candleSeries.setData([
      { time: "2024-06-12", open: 3.1, high: 3.3, low: 3.0, close: 3.2 },
      { time: "2024-06-13", open: 3.2, high: 3.4, low: 3.1, close: 3.3 },
      { time: "2024-06-14", open: 3.3, high: 3.5, low: 3.2, close: 3.4 },
    ]);

    const resize = () => {
      chart.applyOptions({ width: chartRef.current!.clientWidth });
    };

    window.addEventListener("resize", resize);
    return () => {
      chart.remove();
      window.removeEventListener("resize", resize);
    };
  }, [symbol]);

  return (
    <div className="bg-white p-4 rounded-xl shadow h-full">
      <h2 className="text-lg font-semibold mb-2">📊 Gráfico de Velas ({symbol})</h2>
      <div ref={chartRef} className="w-full" />
    </div>
  );
};

export default CandleChart;
