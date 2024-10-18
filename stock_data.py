# stock_analyzer_app.py
import streamlit as st
import yfinance as yf


def fetch_stock_info(ticker):
    stock = yf.Ticker(ticker)
    return stock.info


def fetch_historical_data(ticker, time_period):
    stock = yf.Ticker(ticker)
    return stock.history(period=time_period)


@st.cache_data
def get_stock_data(ticker, time_period):
    try:
        stock_info = fetch_stock_info(ticker)
        historical_data = fetch_historical_data(ticker, time_period)
        return stock_info, historical_data

    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return None, None
