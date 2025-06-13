import numpy as np
import talib
from services.binance_service import get_ohlc
from services import notifier_service


# --- Indicador 1: Squared Diff Mean (SDM) ---
def squared_diff_mean(prices: np.ndarray, window: int = 14) -> float:
    if len(prices) < window + 1:
        return None
    diffs = np.diff(prices[-(window + 1) :])
    squared_diffs = diffs**2
    sdm = np.mean(squared_diffs)
    return sdm


# --- Indicador 2: Entropy Divergence (ED) ---
def entropy_divergence(prices, window=14):
    sma = np.convolve(prices, np.ones(window) / window, mode="valid")
    min_len = min(len(prices), len(sma))
    p = prices[-min_len:]
    q = sma[-min_len:]

    p_norm = p / np.sum(p)
    q_norm = q / np.sum(q)

    p_norm = np.where(p_norm == 0, 1e-10, p_norm)
    q_norm = np.where(q_norm == 0, 1e-10, q_norm)

    m = 0.5 * (p_norm + q_norm)
    kl_pm = np.sum(p_norm * np.log(p_norm / m))
    kl_qm = np.sum(q_norm * np.log(q_norm / m))
    js_divergence = 0.5 * (kl_pm + kl_qm)

    return js_divergence


# --- Indicador 3: Recursive Envelope (RE) ---
def recursive_envelope(prices, period=14, deviation=0.02):
    ema = talib.EMA(prices, timeperiod=period)
    upper_envelope = ema * (1 + deviation)
    lower_envelope = ema * (1 - deviation)
    return upper_envelope, lower_envelope


# --- Detecta padrões de candlestick ---
def detect_candlestick_patterns(highs, lows, opens, closes):
    patterns = {
        "hammer": talib.CDLHAMMER,
        "shooting_star": talib.CDLSHOOTINGSTAR,
        "bullish_engulfing": talib.CDLENGULFING,
        "bearish_engulfing": talib.CDLENGULFING,
        "doji": talib.CDLDOJI,
    }

    detected = {}

    for name, func in patterns.items():
        results = func(opens, highs, lows, closes)
        last = results[-1]
        if last != 0:
            detected[name] = last  # 100 para bullish, -100 para bearish, etc.

    return detected


def analyze_symbol(symbol):
    try:
        ohlc = get_ohlc(symbol)
        opens = np.array(ohlc["opens"])
        highs = np.array(ohlc["highs"])
        lows = np.array(ohlc["lows"])
        closes = np.array(ohlc["closes"])

        rsi = talib.RSI(closes, timeperiod=14)[-1]
        ema_fast = talib.EMA(closes, timeperiod=9)[-1]
        ema_slow = talib.EMA(closes, timeperiod=21)[-1]

        adx = talib.ADX(highs, lows, closes, timeperiod=14)[-1]
        slowk, slowd = talib.STOCH(
            highs,
            lows,
            closes,
            fastk_period=14,
            slowk_period=3,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0,
        )
        atr = talib.ATR(highs, lows, closes, timeperiod=14)[-1]

        sdm = squared_diff_mean(closes)
        ed = entropy_divergence(closes)
        upper_env, lower_env = recursive_envelope(closes)

        price_now = closes[-1]
        upper = upper_env[-1]
        lower = lower_env[-1]

        recent_high = np.max(closes[-20:])
        recent_low = np.min(closes[-20:])
        fib_382 = recent_low + 0.382 * (recent_high - recent_low)
        fib_618 = recent_low + 0.618 * (recent_high - recent_low)

        recommendation = "HOLD"

        # Detectar padrões
        patterns = detect_candlestick_patterns(highs, lows, opens, closes)

        # Ajustar recomendação se padrão relevante encontrado
        if "hammer" in patterns and patterns["hammer"] > 0:
            print(f"{symbol}: Padrão Martelo detectado - possível reversão de alta")
            recommendation = "BUY"
            notifier_service.notify_buy(symbol, price_now)

        if "shooting_star" in patterns and patterns["shooting_star"] < 0:
            print(f"{symbol}: Estrela cadente detectada - possível reversão de baixa")
            recommendation = "SELL"
            notifier_service.notify_sell(symbol, price_now)

        # Condições para BUY
        buy_conditions = [
            rsi < 30,
            price_now < fib_382,
            ema_fast > ema_slow,
            price_now < lower,
            sdm is not None and sdm > 0.0005,
            ed is not None and ed > 0.05,
            adx > 25,
            slowk[-1] < 20,
        ]
        if all(buy_conditions) and recommendation == "HOLD":
            recommendation = "BUY"
            notifier_service.notify_buy(symbol, price_now)

        # Condições para SELL
        sell_conditions = [
            rsi > 70,
            price_now > fib_618,
            ema_fast < ema_slow,
            price_now > upper,
            sdm is not None and sdm < 0.0001,
            ed is not None and ed < 0.01,
            adx > 25,
            slowk[-1] > 80,
        ]
        if all(sell_conditions) and recommendation == "HOLD":
            recommendation = "SELL"
            notifier_service.notify_sell(symbol, price_now)

        print(
            f"🔎 {symbol}: RSI={rsi:.2f} EMA9={ema_fast:.2f} EMA21={ema_slow:.2f} "
            f"ADX={adx:.2f} StochK={slowk[-1]:.2f} ATR={atr:.2f} "
            f"SDM={sdm:.6f} ED={ed:.6f} Price={price_now:.2f} UpperEnv={upper:.2f} LowerEnv={lower:.2f} "
            f"Fib382={fib_382:.2f} Fib618={fib_618:.2f} Rec={recommendation} Patterns={patterns}"
        )

        return {
            "symbol": symbol,
            "RSI": round(rsi, 2),
            "EMA9": round(ema_fast, 4),
            "EMA21": round(ema_slow, 4),
            "ADX": round(adx, 2),
            "StochK": round(slowk[-1], 2),
            "ATR": round(atr, 2),
            "SDM": round(sdm, 6) if sdm is not None else None,
            "ED": round(ed, 6) if ed is not None else None,
            "Price": round(price_now, 4),
            "UpperEnv": round(upper, 4),
            "LowerEnv": round(lower, 4),
            "Fib382": round(fib_382, 4),
            "Fib618": round(fib_618, 4),
            "Recommendation": recommendation,
            "Patterns": patterns,
        }

    except Exception as e:
        print(f"❌ Erro ao analisar {symbol}: {str(e)}")
        return None


def analyze_symbols():
    symbols = [
        "SOLUSDT",
        "SUIUSDT",
        "BTCUSDT",
        "TAOUSDT",
    ]
    for symbol in symbols:
        analyze_symbol(symbol)
