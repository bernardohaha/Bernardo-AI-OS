from backend.agents.agent_swing import analyze_swing

# MOCK: 50 candles com características de RSI baixo, volume alto
candles_rsi_buy = [
    {
        "close": 90 + (i % 3),
        "high": 91 + (i % 3),
        "low": 89 + (i % 3),
        "volume": 1000 + i * 5,
    }
    for i in range(50)
]

# MOCK: 50 candles com subida acentuada para gerar SELL
candles_rsi_sell = [
    {"close": 100 + i, "high": 101 + i, "low": 99 + i, "volume": 900 + i * 4}
    for i in range(50)
]

# MOCK: Lateralização para provocar HOLD
candles_hold = [
    {"close": 100, "high": 101, "low": 99, "volume": 500} for _ in range(50)
]

print("\n=== Teste RSI Buy ===")
result_buy = analyze_swing("MOCKBUY", candles_rsi_buy)
print(result_buy)

print("\n=== Teste RSI Sell ===")
result_sell = analyze_swing("MOCKSELL", candles_rsi_sell)
print(result_sell)

print("\n=== Teste HOLD ===")
result_hold = analyze_swing("MOCKHOLD", candles_hold)
print(result_hold)
