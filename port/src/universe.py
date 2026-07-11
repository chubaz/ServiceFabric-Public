# src/universe.py
import pandas as pd
import numpy as np
import yfinance as yf
import logging
import requests
from src.utils import timeit

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@timeit
def get_sp500_tickers():
    """Fetches the current S&P 500 list from Wikipedia and formats for Yahoo Finance."""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    # Pass a standard browser User-Agent to bypass Wikipedia's 403 Forbidden block
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    table = pd.read_html(response.text)
    df = table[0]
    
    # CRITICAL: Wikipedia uses '.', Yahoo uses '-' (e.g., BRK.B -> BRK-B)
    tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
    return tickers

@timeit
def filter_dynamic_universe(tickers, min_mkt_cap=1e10, top_n=30):
    """
    Optimized filter: Sorts by liquidity first, then lazily evaluates market cap 
    to prevent the N+1 API query bottleneck.
    """
    logging.info(f"Filtering universe of {len(tickers)} tickers for size and liquidity...")
    
    # 1. Bulk download prices safely using 20 threads (much faster than False, safer than True)
    # Dialed back to 10 threads to prevent SQLite database locks, and silenced the warning
    data = yf.download(
        tickers, 
        period="5d", 
        interval="1d", 
        group_by='ticker', 
        progress=False, 
        threads=10, 
        auto_adjust=False  # <-- Silences the FutureWarning
    )
    
    # 2. Calculate Liquidity (MDVT) for all stocks in memory (Extremely Fast)
    liquidity_stats = []
    for ticker in tickers:
        try:
            if len(tickers) == 1:
                t_data = data.dropna()
            else:
                if ticker not in data.columns.levels[0]:
                    continue
                t_data = data[ticker].dropna()
                
            if t_data.empty:
                continue
                
            # MDVT = Price * Volume
            mdvt = (t_data['Close'] * t_data['Volume']).median()
            liquidity_stats.append({'ticker': ticker, 'mdvt': mdvt})
                
        except Exception:
            continue
            
    # 3. Sort purely by Liquidity first
    df_liquidity = pd.DataFrame(liquidity_stats).dropna().sort_values(by='mdvt', ascending=False)
    
    # 4. "Lazy" Market Cap Check: Only query the top liquid names until we hit our quota
    final_tickers = []
    logging.info("Checking Market Cap for top liquid candidates...")
    
    for ticker in df_liquidity['ticker']:
        # Stop looping once we have enough valid mega-caps!
        if len(final_tickers) >= top_n:
            break 
            
        try:
            mkt_cap = yf.Ticker(ticker).fast_info.get('marketCap', 0)
            if mkt_cap >= min_mkt_cap:
                final_tickers.append(ticker)
        except Exception:
            continue
            
    logging.info(f"Final Dynamic Universe selected: {len(final_tickers)} highly liquid stocks.")
    return final_tickers