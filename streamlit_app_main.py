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

load_dotenv()

config = os.getenv('api_key')

# Initialize NewsAPI with the API key from the TOML file
newsapi = NewsApiClient(api_key=config)

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
        fig_candlestick = go.Figure()

        # Candlestick plot
        fig_candlestick.add_trace(go.Candlestick(x=historical_data.index,
                                                 open=historical_data['Open'],
                                                 high=historical_data['High'],
                                                 low=historical_data['Low'],
                                                 close=historical_data['Close'],
                                                 name="Candlestick"))

        # SMA plots
        fig_candlestick.add_trace(go.Scatter(x=historical_data.index, y=historical_data['SMA_50'], mode='lines', name='SMA 50', line=dict(color='blue')))
        fig_candlestick.add_trace(go.Scatter(x=historical_data.index, y=historical_data['SMA_200'], mode='lines', name='SMA 200', line=dict(color='red')))

        # EMA plots
        fig_candlestick.add_trace(go.Scatter(x=historical_data.index, y=historical_data['EMA_9'], mode='lines', name='EMA 9', line=dict(color='green')))
        fig_candlestick.add_trace(go.Scatter(x=historical_data.index, y=historical_data['EMA_21'], mode='lines', name='EMA 21', line=dict(color='orange')))

        # Update layout
        fig_candlestick.update_layout(title=f"{ticker} Price Analysis",
                                      xaxis_title="Date",
                                      yaxis_title="Price",
                                      legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

        st.plotly_chart(fig_candlestick)

        # Plot MACD
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=historical_data.index, y=historical_data['MACD'], mode='lines', name='MACD', line=dict(color='green')))
        fig_macd.add_trace(go.Scatter(x=historical_data.index, y=historical_data['Signal'], mode='lines', name='Signal', line=dict(color='orange')))
        fig_macd.add_trace(go.Bar(x=historical_data.index, y=historical_data['MACD_Histogram'], name='MACD Histogram', marker_color='lightblue'))

        fig_macd.update_layout(title=f"{ticker} MACD Analysis",
                               xaxis_title="Date",
                               yaxis_title="MACD",
                               legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

        st.plotly_chart(fig_macd)

        # Plot RSI
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=historical_data.index, y=historical_data['RSI'], mode='lines', name='RSI', line=dict(color='purple')))

        # Add overbought and oversold lines
        fig_rsi.add_shape(type="line",
                          x0=historical_data.index[0], y0=70,
                          x1=historical_data.index[-1], y1=70,
                          line=dict(color="red", dash="dash"))
        fig_rsi.add_shape(type="line",
                          x0=historical_data.index[0], y0=30,
                          x1=historical_data.index[-1], y1=30,
                          line=dict(color="green", dash="dash"))

        fig_rsi.update_layout(title=f"{ticker} RSI Analysis",
                              xaxis_title="Date",
                              yaxis_title="RSI",
                              legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

        st.plotly_chart(fig_rsi)

        # Plot Stochastic Oscillator
        fig_stochastic = go.Figure()
        fig_stochastic.add_trace(go.Scatter(x=historical_data.index, y=historical_data['Stochastic_%K'], mode='lines', name='Stochastic %K', line=dict(color='blue')))
        fig_stochastic.add_trace(go.Scatter(x=historical_data.index, y=historical_data['Stochastic_%D'], mode='lines', name='Stochastic %D', line=dict(color='orange')))

        # Add overbought and oversold lines
        fig_stochastic.add_shape(type="line",
                                 x0=historical_data.index[0], y0=20,
                                 x1=historical_data.index[-1], y1=20,
                                 line=dict(color="red", dash="dash"))
        fig_stochastic.add_shape(type="line",
                                 x0=historical_data.index[0], y0=80,
                                 x1=historical_data.index[-1], y1=80,
                                 line=dict(color="green", dash="dash"))

        fig_stochastic.update_layout(title=f"{ticker} Stochastic Oscillator",
                                     xaxis_title="Date",
                                     yaxis_title="Stochastic %K/%D",
                                     legend=dict(x=0, y=1, traceorder='normal', orientation='h'))

        st.plotly_chart(fig_stochastic)

        # Plot ADX
        fig_adx = go.Figure()
        fig_adx.add_trace(go.Scatter(x=historical_data.index, y=historical_data['ADX'], mode='lines', name='ADX', line=dict(color='purple')))
        fig_adx.update_layout(title=f"{ticker} ADX",
                              xaxis_title="Date",
                              yaxis_title="ADX",
                              legend=dict(x=0, y=1, traceorder='normal', orientation='h'))
        st.plotly_chart(fig_adx)

        # Plot OBV
        fig_obv = go.Figure()
        fig_obv.add_trace(go.Scatter(x=historical_data.index, y=historical_data['OBV'], mode='lines', name='OBV', line=dict(color='brown')))
        fig_obv.update_layout(title=f"{ticker} On-Balance Volume (OBV)",
                              xaxis_title="Date",
                              yaxis_title="OBV",
                              legend=dict(x=0, y=1, traceorder='normal', orientation='h'))
        st.plotly_chart(fig_obv)

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

