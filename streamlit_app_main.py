import stock_functions
import streamlit as st
import yfinance as yf
import stock_data
import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
from newsapi import NewsApiClient
from textblob import TextBlob
from dotenv import load_dotenv

st.set_page_config(page_title="Comprehensive Indian Stock Analyzer", layout="wide")

# Sidebar Inputs
st.sidebar.title("Stock Analyzer Inputs")

ticker_input = st.sidebar.text_input("Enter the Indian stock symbol (e.g., RELIANCE)", value="RELIANCE")
time_interval = st.sidebar.selectbox(
    "Select Time Interval",
    options=["1m", "5m", "15m", "1D", "1W", "1M"],
    index=3  # Default to '1D'
)
time_period = st.sidebar.selectbox(
    "Select Time Period",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"],
    index=3  # Default to '1y'
)
start_date = st.sidebar.date_input("Start Date", datetime(2022, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.today())

if not ticker_input.endswith('.NS'):
    ticker = ticker_input.upper() + '.NS'
else:
    ticker = ticker_input.upper()

st.title("📈 Comprehensive Indian Stock Analyzer")


if "api_key" in st.secrets:
    api_key = st.secrets["api_key"]
else:
    load_dotenv()
    api_key = os.getenv('api_key')

# Initialize NewsAPI with the API key from the TOML file
newsapi = NewsApiClient(api_key=api_key)

# Main execution flow
if st.sidebar.button("Analyze"):
    stock_info, historical_data = stock_data.get_stock_data(ticker, time_period)
    if stock_info is not None and historical_data is not None:
        # Calculate indicators
        historical_data = stock_functions.calculate_indicators(historical_data)

        # Display historical data
        st.subheader(f"Historical Data for {ticker}")
        st.dataframe(historical_data)

        # Analyze and display insights
        analysis_result = stock_functions.analyze_stock(ticker, stock_info, historical_data)
        st.markdown(analysis_result)

        # Plotting with Plotly

        # 1. Candlestick Chart with SMAs and EMAs
        st.subheader("Candlestick Chart with Moving Averages")

        # Creating an expander for 50 and 200 days Moving Averages
        with st.expander("Read more about 50-day and 200-day Moving Averages", expanded=False):
            # Content inside the expander
            st.write("""
            **Moving Averages** are commonly used indicators in technical analysis that help smooth out price data by creating 
            a constantly updated average price. The **50-day Moving Average (MA)** and the **200-day Moving Average (MA)** 
            are two of the most widely used moving averages.

            ### 50-day Moving Average (50-MA)
            - The **50-day Moving Average** is the average of a security's closing prices over the last 50 days. It is used 
            to identify the short-term trend of a stock or asset.
            - **Interpretation**:
            - **Bullish Signal**: When the price crosses above the 50-MA, it may indicate an upward trend.
            - **Bearish Signal**: When the price crosses below the 50-MA, it may suggest a downward trend.

            ### 200-day Moving Average (200-MA)
            - The **200-day Moving Average** is the average of a security's closing prices over the last 200 days. It is often 
            used to identify the long-term trend and assess the overall market direction.
            - **Interpretation**:
            - **Bullish Signal**: When the price crosses above the 200-MA, it may indicate a strong upward trend.
            - **Bearish Signal**: When the price crosses below the 200-MA, it may suggest a significant downward trend.

            ### Moving Average Crossovers
            - **Golden Cross**: When the 50-MA crosses above the 200-MA, it is known as a "Golden Cross," signaling a potential 
            bullish market.
            - **Death Cross**: When the 50-MA crosses below the 200-MA, it is known as a "Death Cross," signaling a potential 
            bearish market.

            ### Limitations
            - **Lagging Indicator**: Both moving averages are lagging indicators, meaning they are based on past prices and 
            may not react quickly to sudden market changes.
            - **Whipsaws**: In a volatile market, moving averages can produce false signals or "whipsaws," requiring traders 
            to use additional indicators for confirmation.
            """)

        fig_candlestick = go.Figure()

        # Candlestick plot (Price movements)
        fig_candlestick.add_trace(go.Candlestick(x=historical_data.index,
                                                 open=historical_data['Open'],
                                                 high=historical_data['High'],
                                                 low=historical_data['Low'],
                                                 close=historical_data['Close'],
                                                 name="Candlestick"))

        # SMA and EMA plots
        fig_candlestick.add_trace(go.Scatter(x=historical_data.index, y=historical_data['SMA_50'], mode='lines', name='SMA 50', line=dict(color='blue')))
        fig_candlestick.add_trace(go.Scatter(x=historical_data.index, y=historical_data['SMA_200'], mode='lines', name='SMA 200', line=dict(color='red')))
        fig_candlestick.add_trace(go.Scatter(x=historical_data.index, y=historical_data['EMA_50'], mode='lines', name='EMA 50', line=dict(color='green')))
        fig_candlestick.add_trace(go.Scatter(x=historical_data.index, y=historical_data['EMA_50'], mode='lines', name='EMA 200', line=dict(color='orange')))

        fig_candlestick.update_layout(title=f"{ticker} Price Analysis",
                                      xaxis_title="Date",
                                      yaxis_title="Price",
                                      legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

        st.plotly_chart(fig_candlestick)

        # Explanation for Candlestick Chart
        st.write("**Candlestick Chart** shows the price movements of the stock over time. Each candle represents the opening, highest, lowest, and closing prices in a given period.")

        # Current Interpretation for Candlestick Chart
        current_price = historical_data['Close'].iloc[-1]
        sma_50 = historical_data['SMA_50'].iloc[-1]
        sma_200 = historical_data['SMA_200'].iloc[-1]
        ema_15 = historical_data['EMA_15'].iloc[-1]
        ema_50 = historical_data['EMA_50'].iloc[-1]

        if current_price < sma_50 and current_price < sma_200:
            trend = "bearish"
        elif current_price > sma_50 and current_price > sma_200:
            trend = "bullish"
        else:
            trend = "mixed"

        st.write(
            f"**Current Interpretation**: The stock is trading below its 50-day and 200-day SMAs, indicating a {trend} trend. The EMA lines suggest recent price trends, where the stock is currently below the shorter-term EMA values, reflecting bearish momentum.")

        # 2. MACD Chart
        st.subheader("MACD (Moving Average Convergence Divergence) Analysis")

        # Creating an expander for MACD
        with st.expander("Read more about MACD (Moving Average Convergence Divergence)", expanded=False):
            # Content inside the expander
            st.write("""
            **MACD** (Moving Average Convergence Divergence) is a trend-following momentum indicator that shows the relationship 
            between two moving averages of a security's price. It helps traders identify potential buy and sell signals.

            ### Calculation of MACD
            The MACD is calculated by subtracting the 26-period Exponential Moving Average (EMA) from the 12-period EMA:

            \[
            \text{MACD} = \text{EMA}_{12} - \text{EMA}_{26}
            \]

            The MACD line is typically plotted along with a 9-day EMA of the MACD, called the **Signal Line**:

            \[
            \text{Signal Line} = \text{EMA}_{9}(\text{MACD})
            \]

            ### Interpretation of MACD
            - **Bullish Signal**: When the MACD crosses above the Signal Line, it may indicate a buy signal.
            - **Bearish Signal**: When the MACD crosses below the Signal Line, it may indicate a sell signal.

            ### Divergence
            - **Bullish Divergence**: Occurs when the price makes a lower low while the MACD makes a higher low, suggesting potential upward momentum.
            - **Bearish Divergence**: Occurs when the price makes a higher high while the MACD makes a lower high, suggesting potential downward momentum.

            ### Limitations
            - **Lagging Indicator**: The MACD is based on historical price data and may lag in rapidly changing markets.
            - **False Signals**: In volatile markets, MACD can produce false signals, requiring confirmation from other indicators.
            """)

        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=historical_data.index, y=historical_data['MACD'], mode='lines', name='MACD', line=dict(color='green')))
        fig_macd.add_trace(go.Scatter(x=historical_data.index, y=historical_data['Signal'], mode='lines', name='Signal', line=dict(color='orange')))
        fig_macd.add_trace(go.Bar(x=historical_data.index, y=historical_data['MACD_Histogram'], name='MACD Histogram', marker_color='lightblue'))

        fig_macd.update_layout(title=f"{ticker} MACD Analysis",
                               xaxis_title="Date",
                               yaxis_title="MACD",
                               legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

        st.plotly_chart(fig_macd)

        # Explanation for MACD Chart
        st.write("**MACD (Moving Average Convergence Divergence)** measures momentum by comparing two moving averages. The MACD line and the Signal line show the direction and strength of the trend.")

        # Current Interpretation for MACD
        macd_value = historical_data['MACD'].iloc[-1]
        signal_value = historical_data['Signal'].iloc[-1]

        if macd_value < signal_value:
            macd_trend = "bearish"
        else:
            macd_trend = "bullish"

        st.write(f"**Current Interpretation**: The MACD is below the Signal line, indicating {macd_trend} momentum. The negative histogram bars further confirm the downward trend.")

        # 3. RSI Chart
        st.subheader("RSI (Relative Strength Index) Analysis")

        # Creating an expander for RSI
        # Creating an expander
        with st.expander("Read more about RSI (Relative Strength Index)", expanded=False):
            # Content inside the expander

            st.write("""
            **RSI** (Relative Strength Index) is a momentum oscillator that measures the speed and change of price movements. 
            It is primarily used to identify overbought or oversold conditions in a market, helping traders assess the strength 
            of a price trend and potential reversal points.

            ### Calculation of RSI
            RSI is calculated using the following formula:

            \[
            \text{RSI} = 100 - \left( \frac{100}{1 + RS} \right)
            \]

            Where:
            - **RS (Relative Strength)** is the average of *x* days' up closes divided by the average of *x* days' down closes. 
            Typically, *x* is set to 14 days.

            ### Interpretation of RSI
            - **Overbought Condition**: An RSI above 70 indicates that a security may be overbought.
            - **Oversold Condition**: An RSI below 30 indicates that a security may be oversold.

            ### Divergence
            - **Bullish Divergence**: Occurs when the price makes a lower low while the RSI makes a higher low.
            - **Bearish Divergence**: Occurs when the price makes a higher high while the RSI makes a lower high.

            ### Limitations
            - **False Signals**: In trending markets, the RSI can remain overbought or oversold for extended periods.
            - **Lagging Indicator**: RSI is based on historical price data and may not always predict future movements accurately.

             https://en.wikipedia.org/wiki/Relative_strength_index

            """)

        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=historical_data.index, y=historical_data['RSI'], mode='lines', name='RSI', line=dict(color='purple')))
        fig_rsi.add_shape(type="line", x0=historical_data.index[0], y0=70, x1=historical_data.index[-1], y1=70, line=dict(color="red", dash="dash"))
        fig_rsi.add_shape(type="line", x0=historical_data.index[0], y0=30, x1=historical_data.index[-1], y1=30, line=dict(color="green", dash="dash"))

        fig_rsi.update_layout(title=f"{ticker} RSI Analysis",
                              xaxis_title="Date",
                              yaxis_title="RSI",
                              legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

        st.plotly_chart(fig_rsi)

        # Explanation for RSI Chart
        st.write("**RSI (Relative Strength Index)** measures the speed and change of price movements, typically used to identify overbought or oversold conditions.")

        # Current Interpretation for RSI
        rsi_value = historical_data['RSI'].iloc[-1]

        if rsi_value < 30:
            rsi_trend = "oversold"
        elif rsi_value > 70:
            rsi_trend = "overbought"
        else:
            rsi_trend = "neutral"

        st.write(f"**Current Interpretation**: The RSI is currently {rsi_trend}, suggesting potential price movement in the opposite direction.")

        # 4. Stochastic Oscillator
        st.subheader("Stochastic Oscillator")

        # Creating an expander for Stochastic Oscillator
        with st.expander("Read more about Stochastic Oscillator", expanded=False):
            # Content inside the expander
            st.write("""
            The **Stochastic Oscillator** is a momentum indicator used in technical analysis that compares a security's 
            closing price to its price range over a specific period of time. It is designed to identify overbought or 
            oversold conditions in a market.

            ### Components
            - **%K Line**: This is the main line of the stochastic oscillator, representing the current closing price in 
            relation to the price range over a specified period.
            - **%D Line**: This is a moving average of the %K line, often used to signal potential buy or sell opportunities.

            ### Calculation
            The Stochastic Oscillator is calculated using the formula:

            \[
            \%K = \frac{(Current\: Close - Lowest\: Low)}{(Highest\: High - Lowest\: Low)} \times 100
            \]

            Where:
            - **Current Close** is the most recent closing price.
            - **Lowest Low** is the lowest price over the specified period.
            - **Highest High** is the highest price over the specified period.

            The **%D** line is typically a 3-period simple moving average of the %K line.

            ### Interpretation
            - **Overbought Condition**: A Stochastic reading above 80 indicates that the security may be overbought and 
            could be due for a price correction.
            - **Oversold Condition**: A reading below 20 suggests that the security may be oversold and could be poised 
            for a price rebound.
            - **Crossovers**: When the %K line crosses above the %D line, it may signal a buy opportunity, while a 
            crossover below may signal a sell opportunity.

            ### Limitations
            - **False Signals**: The Stochastic Oscillator can produce false signals during strong trends, so it is 
            often used in conjunction with other indicators.
            - **Sensitivity**: Short periods can lead to more sensitivity and frequent signals, while longer periods 
            may provide smoother results but may lag.

            The Stochastic Oscillator is a valuable tool for traders looking to gauge momentum and potential reversal points 
            in the market.
            """)

        fig_stochastic = go.Figure()
        fig_stochastic.add_trace(go.Scatter(x=historical_data.index, y=historical_data['Stochastic_%K'], mode='lines', name='Stochastic %K', line=dict(color='blue')))
        fig_stochastic.add_trace(go.Scatter(x=historical_data.index, y=historical_data['Stochastic_%D'], mode='lines', name='Stochastic %D', line=dict(color='orange')))
        fig_stochastic.add_shape(type="line", x0=historical_data.index[0], y0=20, x1=historical_data.index[-1], y1=20, line=dict(color="red", dash="dash"))
        fig_stochastic.add_shape(type="line", x0=historical_data.index[0], y0=80, x1=historical_data.index[-1], y1=80, line=dict(color="green", dash="dash"))

        fig_stochastic.update_layout(title=f"{ticker} Stochastic Oscillator",
                                     xaxis_title="Date",
                                     yaxis_title="Stochastic Values",
                                     legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

        st.plotly_chart(fig_stochastic)

        # Current Interpretation for Stochastic Oscillator
        stochastic_k = historical_data['Stochastic_%K'].iloc[-1]
        stochastic_d = historical_data['Stochastic_%D'].iloc[-1]

        if stochastic_k > stochastic_d:
            stochastic_trend = "bullish"
        else:
            stochastic_trend = "bearish"

        st.write(f"**Current Interpretation**: The %K is crossing {'above' if stochastic_k > stochastic_d else 'below'} the %D line, suggesting {stochastic_trend} momentum.")

        # 5. ADX Analysis
        st.subheader("ADX (Average Directional Index) Analysis")

        # Creating an expander for ADX
        with st.expander("Read more about ADX (Average Directional Index)", expanded=False):
            # Content inside the expander
            st.write("""
            The **Average Directional Index (ADX)** is a technical analysis indicator used to quantify the strength of a 
            trend in a market. Developed by J. Welles Wilder, the ADX helps traders identify whether a market is trending 
            or ranging, aiding in the decision-making process for entering or exiting trades.

            ### Components
            - **ADX Line**: Measures the strength of the trend but does not indicate its direction.
            - **+DI (Positive Directional Indicator)**: Indicates the strength of upward movement.
            - **-DI (Negative Directional Indicator)**: Indicates the strength of downward movement.

            ### Calculation
            The ADX is calculated using the following steps:
            1. Calculate the True Range (TR).
            2. Determine the +DI and -DI:
                \[
                +DI = \frac{(Current\: High - Previous\: High)}{TR} \times 100
                \]
                \[
                -DI = \frac{(Previous\: Low - Current\: Low)}{TR} \times 100
                \]
            3. Smooth the +DI and -DI values.
            4. Calculate the ADX using the smoothed values of +DI and -DI:
                \[
                ADX = \frac{(Difference\: between\: +DI\: and\: -DI)}{(+DI + -DI)} \times 100
                \]

            ### Interpretation
            - **ADX Value Above 20-25**: Indicates a strong trend, whether upward or downward.
            - **ADX Value Below 20**: Suggests a weak or non-trending market.
            - **Crossovers**: 
                - When +DI crosses above -DI, it indicates a potential buy signal.
                - When -DI crosses above +DI, it indicates a potential sell signal.

            ### Limitations
            - **Lagging Indicator**: The ADX is based on past price data, which means it can lag behind current price movements.
            - **Does Not Indicate Direction**: While ADX shows trend strength, it does not provide information about trend direction, making it essential to use it alongside other indicators.

            The ADX is a useful tool for traders to assess the strength of a trend and make informed decisions about their trades.
            """)

        fig_adx = go.Figure()
        fig_adx.add_trace(go.Scatter(x=historical_data.index, y=historical_data['ADX'], mode='lines', name='ADX', line=dict(color='blue')))
        fig_adx.add_shape(type="line", x0=historical_data.index[0], y0=30, x1=historical_data.index[-1], y1=30, line=dict(color="red", dash="dash"))

        fig_adx.update_layout(title=f"{ticker} ADX Analysis",
                              xaxis_title="Date",
                              yaxis_title="ADX",
                              legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

        st.plotly_chart(fig_adx)

        # Current Interpretation for ADX
        adx_value = historical_data['ADX'].iloc[-1]

        if adx_value > 30:
            adx_trend = "strong"
        else:
            adx_trend = "weak"

        st.write(f"**Current Interpretation**: The ADX value is {adx_value}, indicating a {adx_trend} trend.")

        # 6. OBV Analysis
        st.subheader("OBV (On-Balance Volume) Analysis")

        # Creating an expander for OBV
        with st.expander("Read more about OBV (On-Balance Volume) Analysis", expanded=False):
            # Content inside the expander
            st.write("""
            **On-Balance Volume (OBV)** is a technical analysis indicator that uses volume flow to predict changes in stock price. 
            Developed by Joseph Granville, the OBV provides insights into the strength of price movements based on volume trends.

            ### How OBV Works
            - The core principle of OBV is that volume precedes price movement. Thus, if a security is seeing an increase in volume 
            without a corresponding change in price, it suggests that the price will eventually move in the direction of the volume.

            ### Calculation
            The OBV is calculated using the following formula:
            - If the closing price is higher than the previous closing price:
                \[
                OBV = Previous\: OBV + Current\: Volume
                \]
            - If the closing price is lower than the previous closing price:
                \[
                OBV = Previous\: OBV - Current\: Volume
                \]
            - If the closing price is the same:
                \[
                OBV = Previous\: OBV
                \]

            ### Interpretation
            - **Rising OBV**: Indicates that volume is increasing on up days, suggesting buying pressure and potential price increases.
            - **Falling OBV**: Indicates that volume is increasing on down days, suggesting selling pressure and potential price declines.
            - **Divergences**: A divergence between OBV and price can signal potential reversals. For example, if the price is making new highs while OBV is not, it may indicate weakening momentum.

            ### Limitations
            - **Lagging Indicator**: OBV is based on historical volume data, meaning it can lag behind current price movements.
            - **Market Conditions**: The effectiveness of OBV can vary in different market conditions, making it essential to use it in conjunction with other indicators.

            OBV is a valuable tool for traders seeking to understand the relationship between volume and price movements, helping them make informed trading decisions.
            """)

        fig_obv = go.Figure()
        fig_obv.add_trace(go.Scatter(x=historical_data.index, y=historical_data['OBV'], mode='lines', name='OBV', line=dict(color='green')))

        fig_obv.update_layout(title=f"{ticker} OBV Analysis",
                              xaxis_title="Date",
                              yaxis_title="OBV",
                              legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

        st.plotly_chart(fig_obv)

        # Current Interpretation for OBV
        obv_value = historical_data['OBV'].iloc[-1]
        previous_obv_value = historical_data['OBV'].iloc[-2]

        if obv_value > previous_obv_value:
            obv_trend = "accumulation"
        else:
            obv_trend = "distribution"

        st.write(f"**Current Interpretation**: The OBV trend indicates {obv_trend}, suggesting the sentiment of investors regarding buying or selling the stock.")

        # News Section
        st.subheader("Latest News")
        news = newsapi.get_everything(q=ticker_input, language='en', sort_by='publishedAt')
        for article in news['articles'][:5]:  # Display top 5 articles
            st.markdown(f"### [{article['title']}]({article['url']})")
            st.markdown(f"**Source:** {article['source']['name']} | **Published At:** {article['publishedAt']}")
            st.markdown(f"{article['description']}\n")

        # Sentiment Analysis
        st.subheader("Sentiment Analysis")
        news_articles = newsapi.get_everything(q=ticker_input, language='en', sort_by='relevancy')
        sentiments = []

        for article in news_articles['articles']:
            analysis = TextBlob(article['title'])
            sentiments.append(analysis.sentiment.polarity)  # Get sentiment polarity

        # Display average sentiment score
        average_sentiment = np.mean(sentiments) if sentiments else 0
        sentiment_label = "Positive" if average_sentiment > 0 else "Negative" if average_sentiment < 0 else "Neutral"

        # Display the average sentiment score and label
        st.write(f"Average Sentiment Score: {average_sentiment:.2f} ({sentiment_label})")

        # Add specific messages based on sentiment score
        if average_sentiment > 0.1:
            st.write(f"The overall sentiment is strongly positive, indicating optimistic news about {ticker}.")
        elif 0 < average_sentiment <= 0.1:
            st.write(f"The overall sentiment is slightly positive, suggesting a generally favorable outlook on {ticker}.")
        elif average_sentiment < -0.1:
            st.write(f"The overall sentiment is strongly negative, indicating pessimistic news about {ticker}.")
        elif -0.1 < average_sentiment < 0:
            st.write(f"The overall sentiment is slightly negative, suggesting some concerns regarding {ticker}.")
        else:
            st.write(f"The sentiment is neutral, indicating mixed or no significant sentiment about {ticker}.")

if st.sidebar.button("Clear Analysis"):
    st.session_state.clear()
