import streamlit as st
from ta import momentum
from ta import volume
from ta import trend
import numpy as np


# Function to categorize market cap
def get_cap_category(market_cap_value):
    if isinstance(market_cap_value, (int, float)):
        cap_in_billion = market_cap_value / 1e9
        if cap_in_billion > 100:
            return 'large'
        else:
            return 'mid to small'
    return 'unknown'


# Function to calculate technical indicators
def calculate_indicators(df):
    # Existing indicators
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['RSI'] = calculate_rsi(df['Close'])
    df = calculate_macd(df)

    # New Indicators

    # 1. EMA Crossovers
    df['EMA_15'] = df['Close'].ewm(span=15, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_Crossover'] = df['EMA_15'] > df['EMA_50']

    # 2. Stochastic Oscillator
    stochastic = momentum.StochasticOscillator(
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        window=14,
        smooth_window=3
    )
    df['Stochastic_%K'] = stochastic.stoch()
    df['Stochastic_%D'] = stochastic.stoch_signal()
    df['Stochastic_Signal'] = df['Stochastic_%K'] > df['Stochastic_%D']

    # 3. On-Balance Volume (OBV)
    obv = volume.OnBalanceVolumeIndicator(close=df['Close'], volume=df['Volume'])
    df['OBV'] = obv.on_balance_volume()

    # 4. Average Directional Index (ADX)
    adx = trend.ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=14)
    df['ADX'] = adx.adx()
    df['ADX_Pos'] = adx.adx_pos()
    df['ADX_Neg'] = adx.adx_neg()

    return df


def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(df, fast=12, slow=26, signal=9):
    df['EMA_fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
    df['EMA_slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = df['EMA_fast'] - df['EMA_slow']
    df['Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['Signal']
    return df


def avg_obv_last_n_days(obv_series, n):
    last_n_days_obv = obv_series.iloc[-n:]
    weights = np.arange(1, n + 1)

    avg_obv_last_n_days = np.dot(last_n_days_obv, weights) / weights.sum()

    return avg_obv_last_n_days


def analyze_stock(ticker, stock, df):
    try:
        # Current Indicators
        current_price = df['Close'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        sma_200 = df['SMA_200'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        macd = df['MACD'].iloc[-1]
        signal = df['Signal'].iloc[-1]
        ema_15 = df['EMA_15'].iloc[-1]
        ema_50 = df['EMA_50'].iloc[-1]
        stochastic_k = df['Stochastic_%K'].iloc[-1]
        stochastic_d = df['Stochastic_%D'].iloc[-1]
        stochastic_signal = df['Stochastic_Signal'].iloc[-1]
        obv = df['OBV'].iloc[-1]
        obv_short = avg_obv_last_n_days(df['OBV'], 50)
        obv_long = avg_obv_last_n_days(df['OBV'], 200)
        adx = df['ADX'].iloc[-1]

        adx_pos = df['ADX_Pos'].iloc[-1]
        adx_neg = df['ADX_Neg'].iloc[-1]

        # Fundamental Indicators
        pe_ratio = stock.get('trailingPE', None)
        dividend_yield = stock.get('dividendYield', None)
        market_cap_value = stock.get('marketCap', None)

        pe_ratio_display = f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else 'N/A'
        dividend_yield_display = f"{dividend_yield * 100:.2f}%" if isinstance(dividend_yield, (int, float)) else 'N/A'
        market_cap_display = f"₹{market_cap_value / 1e9:.2f} billion" if isinstance(market_cap_value, (int, float)) else 'N/A'

        cap_category = get_cap_category(market_cap_value)

        # Determine Trend and Momentum
        is_bullish_trend = ema_15 > ema_50 and sma_50 > sma_200
        is_bearish_trend = ema_15 < ema_50 and sma_50 < sma_200
        is_strong_trend = adx > 25

        # Buy Signal Criteria
        buy_signal = (
                is_bullish_trend and
                obv_short > obv_long and  # OBV is rising
                is_strong_trend
        )

        # Sell Signal Criteria
        sell_signal = (
                is_bearish_trend and
                obv_short < obv_long and  # OBV is falling
                is_strong_trend
        )

        # Recommendation Logic
        if buy_signal:
            recommendation = "BUY"
            recommendation_reason = "All buy signal criteria met."
        elif sell_signal:
            recommendation = "SELL"
            recommendation_reason = "All sell signal criteria met."
        else:
            recommendation = "HOLD"
            recommendation_reason = "No clear buy or sell signal."

        # Recommendation Badge
        if recommendation == "BUY":
            recommendation_badge = '🟢 BUY'
        elif recommendation == "SELL":
            recommendation_badge = '🔴 SELL'
        else:
            recommendation_badge = '🟡 HOLD'

        insights: str = f"""**Analysis for {ticker}:**

### Technical Analysis:
1. **Current Price:** ₹{current_price:.2f}
2. **50-day SMA:** ₹{sma_50:.2f}
3. **200-day SMA:** ₹{sma_200:.2f}
4. **RSI:** {rsi:.2f}
5. **MACD:** {macd:.2f}
6. **MACD Signal:** {signal:.2f}
7. **EMA 15:** ₹{ema_15:.2f}
8. **EMA 50:** ₹{ema_50:.2f}
9. **Stochastic %K:** {stochastic_k:.2f}
10. **Stochastic %D:** {stochastic_d:.2f}
11. **OBV:** {obv:.2f}
12. **ADX:** {adx:.2f}

### Fundamental Analysis:
1. **Market Cap:** {market_cap_display}
2. **P/E Ratio:** {pe_ratio_display}
3. **Dividend Yield:** {dividend_yield_display}
4. **52-week High:** ₹{df['Close'].max():.2f}
5. **52-week Low:** ₹{df['Close'].min():.2f}
6. **Average Daily Volume:** {df['Volume'].mean():.0f}

### Key Insights and Recommendation:
{ticker} is currently trading at ₹{current_price:.2f}.

**Technical Outlook:**
# - The stock is trading {'above' if is_bullish_trend else 'below'} its 50-day and 200-day moving averages, indicating a {'bullish' if is_bullish_trend else 'bearish'} trend.
- The RSI at {rsi:.2f} suggests the stock is {'overbought' if rsi > 70 else 'oversold' if rsi < 30 else 'neutral'}.
- The MACD ({macd:.2f}) is {'above' if macd > signal else 'below'} its signal line ({signal:.2f}), suggesting {'bullish' if macd > signal else 'bearish'} momentum.
- The Stochastic Oscillator shows {'oversold conditions' if stochastic_k < 20 else 'overbought conditions' if stochastic_k > 80 else 'neutral conditions'}, with {'%K crossing above %D' if stochastic_signal else '%K crossing below %D'}.
- OBV is {'rising, indicating accumulation.' if obv_short > obv_long else 'falling, indicating distribution.'}
- The ADX at {adx:.2f} confirms a {'strong' if is_strong_trend else 'weak'} trend.

**Fundamental Considerations:**
- With a market cap of {market_cap_display}, this is a {'large' if cap_category == 'large' else 'mid to small'} cap stock.
- The P/E ratio of {pe_ratio_display} {'suggests a premium valuation' if pe_ratio != 'N/A' and float(pe_ratio_display) > 25 else 'indicates a potentially undervalued stock' if pe_ratio != 'N/A' and float(pe_ratio_display) < 15 else 'is within a normal range'}.

**Recommendation:**
Based on the analysis, the current recommendation for {ticker} is to **{recommendation_badge}**.
**Reason:** {recommendation_reason}

*Note: These insights are based on historical data and technical analysis. Always conduct your own research or consult with a financial advisor before making investment decisions.*
"""

        return insights

    except Exception as e:
        st.error(f"Error in analysis: {str(e)}")
        return str(e)
