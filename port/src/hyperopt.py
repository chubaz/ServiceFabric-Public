# src/hyperopt.py
import pandas as pd
import numpy as np
import logging
from src.utils import timeit
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_weight_grid(step=0.10):
    """
    Generates all possible combinations of 3 factor weights that sum to 1.0.
    """
    grid = []
    values = np.arange(0.0, 1.0 + step, step)
    
    for w_mom in values:
        for w_vol in values:
            for w_qual in values:
                # Keep only combinations that sum to exactly 1.0 
                if np.isclose(w_mom + w_vol + w_qual, 1.0):
                    grid.append({'mom': w_mom, 'vol': w_vol, 'qual': w_qual})
    
    logging.info(f"Generated {len(grid)} hyperparameter combinations.")
    return grid

def walk_forward_optimization(z_mom, z_vol, z_qual, prices, lookback_months=12):
    """
    Performs Walk-Forward Validation to dynamically find the best factor weights.
    Evaluates the 'Top 10' equal-weight return of each grid combo in the training window.
    """
    logging.info(f"Starting Walk-Forward Optimization (Lookback: {lookback_months}M)...")
    
    # 1. Prepare Data at a Monthly Frequency
    z_mom_m = z_mom.resample('BME').last()
    z_vol_m = z_vol.resample('BME').last()
    z_qual_m = z_qual.resample('BME').last()
    
    # Calculate 1-month forward returns for evaluation
    monthly_prices = prices.resample('BME').last()
    fwd_returns = monthly_prices.pct_change().shift(-1)
    
    grid = generate_weight_grid(step=0.10)
    dates = z_mom_m.index
    
    dynamic_scores_list = []
    weight_history = []
    
    # 2. Walk Forward Through Time
    # We start at 'lookback_months' because we need initial training data
    for i in range(lookback_months, len(dates)):
        current_date = dates[i]
        
        # The Training Window (e.g., the last 12 months)
        train_dates = dates[i - lookback_months : i]
        
        best_sharpe = -np.inf
        best_weights = None
        
        # 3. Grid Search within the Training Window
        for w in grid:
            # Build the signal for the training period
            train_scores = (w['mom'] * z_mom_m.loc[train_dates] + 
                            w['vol'] * z_vol_m.loc[train_dates] + 
                            w['qual'] * z_qual_m.loc[train_dates])
            
            # Evaluate this signal's predictive power
            strat_returns = []
            for td in train_dates:
                td_scores = train_scores.loc[td].dropna().sort_values(ascending=False)
                if len(td_scores) < 10: 
                    continue
                # Take the Top 10 stocks and see how they performed the NEXT month
                top10_tickers = td_scores.head(10).index
                td_fwd_ret = fwd_returns.loc[td, top10_tickers].mean()
                strat_returns.append(td_fwd_ret)
                
            # Calculate Training Sharpe Ratio (Annualized)
            if len(strat_returns) > 0:
                mean_ret = np.mean(strat_returns)
                std_ret = np.std(strat_returns)
                sharpe = (mean_ret / std_ret) * np.sqrt(12) if std_ret > 0 else 0
            else:
                sharpe = 0
                
            # Update winner
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = w
                
        # 4. Apply the Winning Weights to the Current Out-of-Sample Month
        current_score = (best_weights['mom'] * z_mom_m.loc[[current_date]] + 
                         best_weights['vol'] * z_vol_m.loc[[current_date]] + 
                         best_weights['qual'] * z_qual_m.loc[[current_date]])
                         
        dynamic_scores_list.append(current_score)
        weight_history.append({'Date': current_date, **best_weights})
        
    # Combine results
    dynamic_composite_scores = pd.concat(dynamic_scores_list)
    weight_history_df = pd.DataFrame(weight_history).set_index('Date')
    
    return dynamic_composite_scores, weight_history_df

def walk_forward_risk_parity(z_mom, z_vol, z_qual, prices, lookback_months=12):
    """
    Method B: Risk Parity Factor Weighting.
    Weights factors inversely proportional to their historical return volatility.
    """
    logging.info(f"Starting Risk Parity Walk-Forward (Lookback: {lookback_months}M)...")
    
    z_mom_m = z_mom.resample('BME').last()
    z_vol_m = z_vol.resample('BME').last()
    z_qual_m = z_qual.resample('BME').last()
    
    monthly_prices = prices.resample('BME').last()
    fwd_returns = monthly_prices.pct_change().shift(-1)
    
    dates = z_mom_m.index
    dynamic_scores_list = []
    weight_history = []
    
    for i in range(lookback_months, len(dates)):
        current_date = dates[i]
        train_dates = dates[i - lookback_months : i]
        
        factor_returns = {'mom': [], 'vol': [], 'qual': []}
        
        # 1. Simulate the historical performance of each PURE factor
        for td in train_dates:
            for factor_name, factor_z in [('mom', z_mom_m), ('vol', z_vol_m), ('qual', z_qual_m)]:
                scores = factor_z.loc[td].dropna().sort_values(ascending=False)
                if len(scores) >= 10:
                    top10 = scores.head(10).index
                    ret = fwd_returns.loc[td, top10].mean()
                    factor_returns[factor_name].append(ret)
                    
        # 2. Calculate the standard deviation (risk) of each factor
        risk_mom = np.std(factor_returns['mom']) if len(factor_returns['mom']) > 0 else 1.0
        risk_vol = np.std(factor_returns['vol']) if len(factor_returns['vol']) > 0 else 1.0
        risk_qual = np.std(factor_returns['qual']) if len(factor_returns['qual']) > 0 else 1.0
        
        # Prevent division by zero
        risk_mom = max(risk_mom, 1e-6)
        risk_vol = max(risk_vol, 1e-6)
        risk_qual = max(risk_qual, 1e-6)
        
        # 3. Inverse Volatility Weighting (1 / Risk)
        inv_mom = 1.0 / risk_mom
        inv_vol = 1.0 / risk_vol
        inv_qual = 1.0 / risk_qual
        
        total_inv_risk = inv_mom + inv_vol + inv_qual
        
        # 4. Normalize weights to sum to 1.0
        best_weights = {
            'mom': inv_mom / total_inv_risk,
            'vol': inv_vol / total_inv_risk,
            'qual': inv_qual / total_inv_risk
        }
        
        # 5. Apply to out-of-sample month
        current_score = (best_weights['mom'] * z_mom_m.loc[[current_date]] + 
                         best_weights['vol'] * z_vol_m.loc[[current_date]] + 
                         best_weights['qual'] * z_qual_m.loc[[current_date]])
                         
        dynamic_scores_list.append(current_score)
        weight_history.append({'Date': current_date, **best_weights})
        
    return pd.concat(dynamic_scores_list), pd.DataFrame(weight_history).set_index('Date')

from sklearn.linear_model import Ridge
@timeit
def walk_forward_regression(z_mom, z_vol, z_qual, prices, lookback_months=12):
    """
    Method C: Machine Learning (Ridge Regression).
    Regresses forward 1-month returns against factor exposures to dynamically find optimal weights.
    """
    logging.info(f"Starting ML Regression Walk-Forward (Lookback: {lookback_months}M)...")
    
    z_mom_m = z_mom.resample('BME').last()
    z_vol_m = z_vol.resample('BME').last()
    z_qual_m = z_qual.resample('BME').last()
    
    monthly_prices = prices.resample('BME').last()
    fwd_returns = monthly_prices.pct_change().shift(-1)
    
    dates = z_mom_m.index
    dynamic_scores_list = []
    weight_history = []
    
    # Initialize Ridge Regression (alpha is the L2 penalty strength)
    model = Ridge(alpha=1.0, fit_intercept=False)
    
    for i in range(lookback_months, len(dates)):
        current_date = dates[i]
        train_dates = dates[i - lookback_months : i]
        
        X_train = []
        y_train = []
        
        # 1. Build the Training Dataset (Flattening the cross-section)
        for td in train_dates:
            # Get valid tickers that have all 3 factor scores and a forward return
            valid_data = pd.DataFrame({
                'mom': z_mom_m.loc[td],
                'vol': z_vol_m.loc[td],
                'qual': z_qual_m.loc[td],
                'ret': fwd_returns.loc[td]
            }).dropna()
            
            if not valid_data.empty:
                X_train.append(valid_data[['mom', 'vol', 'qual']].values)
                y_train.append(valid_data['ret'].values)
                
        if len(X_train) == 0:
            continue
            
        # Concatenate all months and stocks into one giant training set
        X = np.vstack(X_train)
        y = np.concatenate(y_train)
        
        # 2. Fit the ML Model
        model.fit(X, y)
        coefs = model.coef_
        
        # 3. Convert Coefficients to Long-Only Weights
        # ML might say "short momentum" (negative coef). For our long-only strategy, 
        # we clip negatives to 0, then normalize so they sum to 1.0.
        raw_weights = np.clip(coefs, 0.001, None) # Floor at 0.001 to avoid exact zeros
        normalized_weights = raw_weights / np.sum(raw_weights)
        
        best_weights = {
            'mom': normalized_weights[0],
            'vol': normalized_weights[1],
            'qual': normalized_weights[2]
        }
        
        # 4. Apply to out-of-sample month
        current_score = (best_weights['mom'] * z_mom_m.loc[[current_date]] + 
                         best_weights['vol'] * z_vol_m.loc[[current_date]] + 
                         best_weights['qual'] * z_qual_m.loc[[current_date]])
                         
        dynamic_scores_list.append(current_score)
        weight_history.append({'Date': current_date, **best_weights})
        
    return pd.concat(dynamic_scores_list), pd.DataFrame(weight_history).set_index('Date')