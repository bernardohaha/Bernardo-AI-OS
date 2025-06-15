import sys
import os

# Adiciona o diretório pai (raiz do projeto) ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi import APIRouter
from pydantic import BaseModel
from services.binance_service import (
    get_portfolio,
    get_candles,
    get_portfolio_with_value,
)
from services.suggestion_engine import analyze_symbol
from services.logger_service import log_suggestion, get_logs
from services.advisor_service import get_advisor_logs
from services.advisor.portfolio_advisor import analyze_portfolio
from services.advisor.swing_advisor import analyze_swing
from services import advisor_service, binance_service, order_service
from services import executor_service
from services.market_analysis_service import analyze_orderbook_pressure
from services.advisor_service import get_portfolio
from backend.agents.supervisor_agent import supervisor_agent
from backend.services.candlestick_patterns_service import detect_candlestick_patterns
from backend.services.binance_service import get_trade_history
from backend.services.portfolio_service import build_positions
from services.order_service import get_real_orders
from services.position_service import get_all_positions


from apscheduler.schedulers.background import BackgroundScheduler
import numpy as np
import pandas as pd
import talib
import atexit
from dotenv import load_dotenv
from backend.services.ohlcv_stream_service import start_streaming_ohlcv

start_streaming_ohlcv()

from fastapi.middleware.cors import CORSMiddleware

# FastAPI instance
app = FastAPI()
router = APIRouter()


# Middleware CORS (para o teu frontend funcionar sem problemas de CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carregar variáveis de ambiente
load_dotenv()


# ---------- Definir a função antes do scheduler ----------
def run_ai_advisor():
    print("AI Advisor está a correr automaticamente...")
    portfolio = binance_service.get_portfolio()
    advisor_service.auto_generate_orders(portfolio)
    print("Ordens AI atualizadas.")


# ---------- Iniciar o Scheduler ----------
scheduler = BackgroundScheduler()
scheduler.add_job(run_ai_advisor, "interval", hours=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# ---------- Endpoints ----------


@app.get("/portfolio")
async def portfolio():
    data = get_portfolio_with_value()
    return data


class CandleData(BaseModel):
    symbol: str
    prices: list


@app.post("/analyze")
async def analyze_candle(data: CandleData):
    prices = np.array(data.prices)
    rsi = talib.RSI(prices, timeperiod=14)[-1]
    ema_fast = talib.EMA(prices, timeperiod=9)[-1]
    ema_slow = talib.EMA(prices, timeperiod=21)[-1]

    recommendation = "HOLD"
    if rsi < 30 and ema_fast > ema_slow:
        recommendation = "BUY"
    elif rsi > 70 and ema_fast < ema_slow:
        recommendation = "SELL"

    return {
        "symbol": data.symbol,
        "RSI": round(rsi, 2),
        "EMA9": round(ema_fast, 4),
        "EMA21": round(ema_slow, 4),
        "recommendation": recommendation,
    }


@app.get("/analyze-binance/{symbol}")
async def analyze_binance(symbol: str):
    closes = get_candles(symbol)
    prices = np.array(closes)
    rsi = talib.RSI(prices, timeperiod=14)[-1]
    ema_fast = talib.EMA(prices, timeperiod=9)[-1]
    ema_slow = talib.EMA(prices, timeperiod=21)[-1]

    recommendation = "HOLD"
    if rsi < 30 and ema_fast > ema_slow:
        recommendation = "BUY"
    elif rsi > 70 and ema_fast < ema_slow:
        recommendation = "SELL"

    return {
        "symbol": symbol,
        "RSI": round(rsi, 2),
        "EMA9": round(ema_fast, 4),
        "EMA21": round(ema_slow, 4),
        "recommendation": recommendation,
    }


@app.get("/suggestions")
async def generate_suggestions():
    portfolio = get_portfolio()
    suggestions = []
    for asset in portfolio:
        symbol = asset["symbol"]
        if symbol.endswith("USDT"):
            result = analyze_symbol(symbol)
            log_suggestion(result)
            suggestions.append(result)
    return suggestions


@app.get("/logs")
async def logs():
    data = get_logs()
    return data


@app.get("/advisor/run")
async def run_advisor():
    analyze_portfolio()
    return {"status": "Advisor analysis executed."}


@app.get("/advisor/logs")
async def advisor_logs():
    return get_advisor_logs()


@app.get("/advisor/analyze/{symbol}")
async def advisor_analyze(symbol: str):
    result = analyze_symbol(symbol)
    return result


@app.get("/advisor/analyze-portfolio")
async def advisor_analyze_portfolio():
    portfolio = get_portfolio()
    results = []

    for item in portfolio:
        symbol_raw = item["symbol"]
        symbol = symbol_raw.replace("LD", "") + "USDT"

        try:
            results.append(analyze_symbol(symbol))
        except Exception as e:
            print(f"Erro ao analisar {symbol}: {e}")

    return results


@app.get("/swing-advisor/analyze/{symbol}")
async def swing_advisor_analysis(symbol: str):
    report = analyze_swing(symbol)
    return report


@app.get("/portfolio_analysis")
def portfolio_analysis():
    portfolio = binance_service.get_portfolio()
    analysis = advisor_service.get_portfolio_analysis(portfolio)
    return analysis


@app.get("/orders")
def get_orders():
    return order_service.get_orders()


@app.post("/orders")
def add_order(order: dict):
    return order_service.add_order(order)


@app.post("/generate_ai_orders")
def generate_ai_orders():
    portfolio = binance_service.get_portfolio()
    advisor_service.auto_generate_orders(portfolio)
    return {"message": "AI orders generated successfully!"}


@app.post("/execute_orders")
def execute_orders():
    executor_service.execute_orders()
    return {"message": "Orders executed (simulation)."}


@app.get("/orderbook/{symbol}")
async def get_orderbook(symbol: str, limit: int = 10):
    """
    Retorna o order book (bids e asks) de um par, como SUIUSDT ou SOLUSDT.
    """
    orderbook = binance_service.get_order_book(symbol, limit)
    if orderbook:
        return orderbook
    return {"error": f"Não foi possível obter o orderbook de {symbol}"}


@app.get("/orderbook/analysis/{symbol}")
async def orderbook_analysis(symbol: str, limit: int = 10):
    return analyze_orderbook_pressure(symbol, limit)


@app.get("/candles/{symbol}")
async def get_candlestick_data(symbol: str, interval: str = "1h", limit: int = 100):
    try:
        candles = binance_service.get_candles(symbol.upper(), interval, limit)
        return candles
    except Exception as e:
        return {"error": f"Erro ao obter candles de {symbol}: {str(e)}"}


@app.get("/supervisor/{symbol}")
def get_supervisor_insight(symbol: str):
    return supervisor_agent(symbol)


@app.get("/patterns/{symbol}")
def get_patterns(symbol: str, interval: str = "1h"):
    return detect_candlestick_patterns(symbol, interval)


@router.get("/positions")
def positions():
    return get_open_positions()


@app.get("/real_trades/{symbol}")
def real_trades(symbol: str):
    return get_trade_history(symbol)


@app.get("/portfolio_positions/{symbol}")
def portfolio_positions(symbol: str):
    return build_positions(symbol)


@app.get("/real_orders")
def real_orders():
    return get_real_orders()


@app.get("/positions")
def get_positions():
    return get_all_positions()
