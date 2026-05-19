import yfinance as yf
import pandas as pd
from agents import llm, safe_parse_json
from state import TradeBuddyState, AgentSignal

def compute_rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss
    return round(float((100 - (100/(1+rs))).iloc[-1]), 2)

def compute_macd(prices: pd.Series):
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return round(float(macd_line.iloc[-1]), 4), round(float(signal_line.iloc[-1]), 4)

def compute_bollinger(prices: pd.Series, period: int = 20) -> float:
    '''Price position within Bollinger bands:
    0 = lower band
    1 = upper band
    '''
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (2 * std)
    lower = sma - (2 * std)

    # Calculate the band range based on the most recent data point
    band_range = float(upper.iloc[-1]) - float(lower.iloc[-1])

    if band_range == 0:
        return 0.5

    # Return the position of the price within the bands (0 to 1 scale)
    return round((prices.iloc[-1] - float(lower.iloc[-1])) / band_range, 3)


def price_agent(state: TradeBuddyState) -> dict:
    ticker = state["ticker"]
    # Handle crypto vs stock ticker formats for yfinance
    yfin_ticker = f"{ticker}-USD" if state["asset_type"] == "crypto" else ticker

    try:
        # Download 90 days of daily data
        data = yf.download(yfin_ticker, period="90d", interval="1d", progress=False)

        if data.empty:
            return {"agent_signals": [AgentSignal(
                    agent="price",
                    signal="NEUTRAL",
                    confidence=0.0,
                    summary=f"No price data found for {ticker}",
                    raw_data={},
            )]}

        # 1. Process basic price action
        close = data["Close"].squeeze()
        current_price = round(float(close.iloc[-1]), 4)
        price_7d_ago = round(float(close.iloc[-7]), 4)
        change_7d = round(((current_price - price_7d_ago) / price_7d_ago) * 100, 2)

        # 2. Bollinger Band Logic
        rsi = compute_rsi(close)
        macd_line, signal_line = compute_macd(close)
        bollinger = compute_bollinger(close)

        raw_data = {
            "current_price": current_price,
            "price_change_7d": change_7d,
            "rsi": rsi,
            "macd_line": macd_line,
            "macd_signal": signal_line,
            "bollinger_position": bollinger,
            "macd_crossover": "positive" if macd_line > signal_line else "negative",
        }


        prompt = f"""You are a technical analyst. Analyze these indicators for {ticker}:
        RSI: {rsi} (below 30 = oversold, above 70 = overbought)
        MACD crossover: {raw_data['macd_crossover']} (positive = bullish, negative = bearish)
        Bollinger Band position: {bollinger} (0 = lower band, 1 = upper band)
        7-day price change: {change_7d}%

        Return ONLY valid JSON with exactly these fields, no other text:
        {{"signal": "BULLISH" or "BEARISH" or "NEUTRAL",
        "confidence": 0.0 to 1.0,
        "summary": "one sentence under 20 words"}}
        """

        response = llm.invoke(prompt)
        result = safe_parse_json(response.content)

        return {"agent_signals": [AgentSignal(
            agent="price",
            signal=result["signal"],
            confidence=float(result["confidence"]),
            summary=result["summary"],
            raw_data=raw_data,

        )]}

    except Exception as e:
        return {"agent_signals": [AgentSignal(
            agent="price",
            signal="NEUTRAL",
            confidence=0.0,
            summary=f"Price agent error : {str(e)[:60]}",
            raw_data={}
        )]}
