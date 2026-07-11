# src/pipeline.py
import pandas as pd
import numpy as np

import sys
import os

# Get the absolute path of the current project root
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.append(root_path)

from src.data_loader import download_price_data, clean_price_data, download_fundamentals
from src.factors import (compute_momentum, compute_volatility, compute_roe, 
                         compute_synthetic_esg, compute_cross_sectional_zscore)
from src.hyperopt import walk_forward_regression
from src.optimizer import generate_optimized_weights
from src.backtest import calculate_portfolio_performance
# src/pipeline.py (Updated excerpt)
from src.universe import get_sp500_tickers, filter_dynamic_universe
from src.utils import timeit

@timeit
def run_research_pipeline(start_date, end_date, universe_size=30, max_weight=0.15, cost_bps=20):
    raw_list = get_sp500_tickers()
    universe = filter_dynamic_universe(raw_list, min_mkt_cap=1e10, top_n=universe_size)
    
    # ... rest of your existing data loading and ML/MVO logic ...
    prices_raw, _ = download_price_data(universe, start_date, end_date)
    prices = clean_price_data(prices_raw)
    daily_returns = prices.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    daily_returns = daily_returns.clip(lower=-0.90, upper=1.0).dropna(how='all')
    fundamentals = download_fundamentals(prices.columns)
    
    # 2. Factor Engineering & Sanitization
    z_mom = compute_cross_sectional_zscore(compute_momentum(prices).replace([np.inf, -np.inf], np.nan).dropna(how='all'))
    z_vol = -compute_cross_sectional_zscore(compute_volatility(daily_returns).replace([np.inf, -np.inf], np.nan).dropna(how='all'))
    
    raw_roe = compute_roe(fundamentals, prices.index).replace([np.inf, -np.inf], np.nan)
    raw_roe = raw_roe.clip(lower=-50, upper=50) 
    z_roe = compute_cross_sectional_zscore(raw_roe.dropna(how='all'))
    
    # 3. Dynamic Signal Generation (Method C: ML Regression)
    # This ensures OOS integrity automatically
    dynamic_scores, factor_weight_history = walk_forward_regression(
        z_mom, z_vol, z_roe, prices, lookback_months=12
    )
    
    # 4. SciPy MVO Optimization
    optimized_weights = generate_optimized_weights(
        dynamic_scores, daily_returns, top_n=20, max_weight=max_weight
    )
    
    # 5. Backtest & Performance
    gross_ret, net_ret = calculate_portfolio_performance(
        optimized_weights, daily_returns, cost_bps=cost_bps
    )
    
    return {
        'net_returns': net_ret,
        'weights': optimized_weights,
        'factor_weights': factor_weight_history,
        'prices': prices
    }