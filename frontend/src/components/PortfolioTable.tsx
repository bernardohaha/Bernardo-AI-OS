import React, { useEffect, useState } from "react"
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"

interface Order {
  price: number
  qty: number
  side: string
  time: number
}

interface PortfolioItem {
  symbol: string
  entry_price: number
  current_price: number
  quantity: number
  profit_usd: number
  profit_percent: number
  suggestion: string
  value_usd: number
  orders?: Order[]
}

const COLORS = [
  "#825C46", "#A9927D", "#4B3F2B", "#E6DDC6", "#988257", "#D9C5A0", "#A47149", "#FFD07B"
]

const PortfolioTable: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("http://localhost:8000/portfolio_analysis")
      .then((res) => res.json())
      .then((data) => {
        const enrichedData = data.map((item: any) => ({
          ...item,
          value_usd: item.current_price * item.quantity
        }))
        setPortfolio(enrichedData)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <p>A carregar portfolio...</p>

  const totalUsd = portfolio.reduce((acc, item) => acc + item.value_usd, 0)

  const suggestionColor = (suggestion: string) => {
    if (suggestion.includes("BUY")) return "text-green-600 font-semibold"
    if (suggestion.includes("SELL")) return "text-red-600 font-semibold"
    return "text-gray-600"
  }

  return (
    <div className="p-6">
      <h3 className="text-xl font-bold mb-4">
        Valor Total em Carteira:{" "}
        <span className="text-green-600">${totalUsd.toFixed(2)}</span>
      </h3>

      <div style={{ width: 400, height: 300, margin: "auto" }}>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={portfolio}
              dataKey="value_usd"
              nameKey="symbol"
              cx="50%"
              cy="50%"
              outerRadius={90}
              fill="#8884d8"
              label={({ symbol, percent }) =>
                `${symbol} (${(percent * 100).toFixed(1)}%)`
              }
            >
              {portfolio.map((_, i) => (
                <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(v: any) => `$${Number(v).toFixed(2)}`} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="overflow-x-auto mt-6">
        <table className="min-w-full border border-gray-200 rounded-xl">
          <thead className="bg-gray-100">
            <tr className="text-left">
              <th className="px-4 py-2">Ativo</th>
              <th>Qtd</th>
              <th>Entrada</th>
              <th>Atual</th>
              <th>Lucro ($)</th>
              <th>Lucro (%)</th>
              <th>Sugestão</th>
              <th>Ordens</th>
            </tr>
          </thead>
          <tbody>
            {portfolio.map((item, index) => (
              <tr key={index} className="border-b">
                <td className="px-4 py-2 font-bold">{item.symbol}</td>
                <td>{item.quantity}</td>
                <td>${item.entry_price.toFixed(2)}</td>
                <td>${item.current_price.toFixed(2)}</td>
                <td className={item.profit_usd >= 0 ? "text-green-600" : "text-red-600"}>
                  ${item.profit_usd.toFixed(2)}
                </td>
                <td className={item.profit_percent >= 0 ? "text-green-600" : "text-red-600"}>
                  {item.profit_percent.toFixed(2)}%
                </td>
                <td className={suggestionColor(item.suggestion)}>{item.suggestion}</td>
                <td>
                  {item.orders && item.orders.length > 0 ? (
                    <details>
                      <summary className="cursor-pointer text-blue-600">Ver</summary>
                      <ul className="text-sm mt-2">
                        {item.orders.slice(0, 5).map((order, i) => (
                          <li key={i}>
                            {order.side} {order.qty} @ ${order.price} —{" "}
                            {new Date(order.time).toLocaleString()}
                          </li>
                        ))}
                      </ul>
                    </details>
                  ) : (
                    "-"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default PortfolioTable
