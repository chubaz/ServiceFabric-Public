import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import quantstats as qs
import sys
import os
from datetime import datetime, timedelta

# --- SYSTEM PATH SETUP ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from src.pipeline import run_research_pipeline
except ImportError as e:
    st.error(f"❌ Module Import Error: {e}")
    st.stop()

# --- THEME DEFINITION (PROFESSIONAL LIGHT) ---
COLORS = {
    "bg_main": "#FFFFFF",
    "bg_card": "#F8F9FA",
    "bg_sidebar": "#F1F3F5",
    "accent": "#007BFF",      # Blue Strategy
    "benchmark": "#DC3545",   # Red Benchmark
    "text_main": "#212529",
    "text_muted": "#6C757D",
    "border": "#DEE2E6",
    "success": "#28A745",
    "warning": "#FFC107"
}

# --- SET PAGE CONFIG ---
st.set_page_config(
    page_title="AlphaStream | Quant Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLORS['bg_main']}; color: {COLORS['text_main']}; }}
    section[data-testid="stSidebar"] {{ background-color: {COLORS['bg_sidebar']}; border-right: 1px solid {COLORS['border']}; }}
    div[data-testid="stMetric"] {{ 
        background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; 
        padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; background-color: transparent; }}
    .stTabs [data-baseweb="tab"] {{ 
        background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; 
        border-bottom: none; border-radius: 8px 8px 0 0; padding: 10px 20px; color: {COLORS['text_muted']}; 
    }}
    .stTabs [aria-selected="true"] {{ background-color: {COLORS['accent']} !important; color: white !important; font-weight: bold; }}
    .stButton>button {{ background-color: {COLORS['accent']}; color: white; border-radius: 8px; width: 100%; font-weight: bold; }}
    div[data-testid="stDataFrame"] {{ border: 1px solid {COLORS['border']}; border-radius: 8px; }}
    h1, h2, h3 {{ color: {COLORS['text_main']} !important; font-family: 'Segoe UI', sans-serif; }}
    .stCaption {{ color: {COLORS['text_muted']} !important; }}
    </style>
    """, unsafe_allow_html=True)

def apply_custom_theme(fig):
    fig.update_layout(
        template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color=COLORS['text_main'],
        xaxis=dict(gridcolor=COLORS['border'], zerolinecolor=COLORS['border'], linecolor=COLORS['border']),
        yaxis=dict(gridcolor=COLORS['border'], zerolinecolor=COLORS['border'], linecolor=COLORS['border']),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h1 style='color:{COLORS['accent']}; font-size: 24px; margin-bottom: 0;'>AlphaStream</h1>", unsafe_allow_html=True)
    st.caption("Professional Quant Terminal")
    st.markdown("---")
    
    st.header("1. Strategy Parameters")
    universe_size = st.slider("Universe Depth (Top N)", 20, 100, 30, help="Number of S&P 500 stocks to consider based on market cap.")
    max_w = st.slider("Max Asset Weight (%)", 5, 30, 15, help="Concentration limit for the optimizer.") / 100.0
    costs = st.slider("Transaction Cost (bps)", 0, 50, 20, help="Fees + Slippage applied per rebalance.")
    
    st.markdown("---")
    st.header("2. Backtest Period")
    # Using fixed dates for now as per current pipeline design
    st.info("OOS Period: 2022-01-01 to 2026-03-31")
    
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🚀 EXECUTE BACKTEST", type="primary")

# --- MAIN DASHBOARD ---
if run_btn:
    try:
        with st.spinner("Executing Research Pipeline (ML Ridge + SciPy MVO)..."):
            # Corrected call: use universe_size, not universe
            results = run_research_pipeline(
                start_date='2022-01-01', 
                end_date='2026-03-31', 
                universe_size=universe_size, 
                max_weight=max_w, 
                cost_bps=costs
            )
            
            strat_returns = results['net_returns']
            
            # Benchmark
            spy_data = yf.download('SPY', start=strat_returns.index[0], end=strat_returns.index[-1], progress=False)
            benchmark_returns = spy_data['Close'].pct_change().dropna()
            if isinstance(benchmark_returns, pd.DataFrame): 
                benchmark_returns = benchmark_returns.iloc[:, 0]
            benchmark_returns.name = "S&P 500"
            
            comp_df = pd.concat([strat_returns, benchmark_returns], axis=1).dropna()
            comp_df.columns = ['Strategy (Net)', 'S&P 500']

            st.title("AlphaStream | Performance Analytics")
            st.markdown("---")

            # --- METRICS ---
            m1, m2, m3, m4 = st.columns(4)
            strat_cagr = qs.stats.cagr(comp_df['Strategy (Net)'])
            bench_cagr = qs.stats.cagr(comp_df['S&P 500'])
            m1.metric("Annualized Return", f"{strat_cagr:.2%}", f"{(strat_cagr - bench_cagr):.2%} Alpha")
            m2.metric("Sharpe Ratio", f"{qs.stats.sharpe(comp_df['Strategy (Net)']):.2f}")
            m3.metric("Max Drawdown", f"{qs.stats.max_drawdown(comp_df['Strategy (Net)']):.2%}", delta_color="inverse")
            m4.metric("Volatility", f"{qs.stats.volatility(comp_df['Strategy (Net)']):.2%}")

            # --- TABS ---
            tab1, tab2, tab3 = st.tabs(["📈 PERFORMANCE", "📊 ML SIGNALS", "🥧 ALLOCATION"])

            with tab1:
                colA, colB = st.columns(2)
                with colA:
                    st.subheader("Cumulative Growth")
                    growth_df = (1 + comp_df).cumprod()
                    fig_growth = px.line(growth_df, color_discrete_map={'Strategy (Net)': COLORS['accent'], 'S&P 500': COLORS['text_muted']})
                    st.plotly_chart(apply_custom_theme(fig_growth), use_container_width=True)
                with colB:
                    st.subheader("Underwater Chart")
                    dd_df = (growth_df / growth_df.cummax()) - 1.0
                    fig_dd = px.area(dd_df, color_discrete_map={'Strategy (Net)': COLORS['benchmark'], 'S&P 500': COLORS['text_muted']})
                    fig_dd.update_traces(fill='tozeroy', opacity=0.3)
                    st.plotly_chart(apply_custom_theme(fig_dd), use_container_width=True)

            with tab2:
                st.subheader("Dynamic Factor Tilts (Ridge Regression)")
                st.markdown("The ML model adaptively weights factors based on trailing performance.")
                fw_df = results['factor_weights']
                fig_fw = px.area(fw_df, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(apply_custom_theme(fig_fw), use_container_width=True)

            with tab3:
                st.subheader("Optimized Target Allocations")
                w_df = results['weights']
                top_cols = w_df.mean().sort_values(ascending=False).index[:15]
                fig_w = px.area(w_df[top_cols], title="Top 15 Historical Weights")
                st.plotly_chart(apply_custom_theme(fig_w), use_container_width=True)
                
                st.markdown("### Latest Portfolio Targets")
                latest_w = w_df.iloc[-1].sort_values(ascending=False)
                st.dataframe(latest_w[latest_w > 0.005].to_frame(name="Weight").style.format("{:.2%}"), use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Pipeline Execution Error: {e}")
        import traceback
        st.expander("Technical Traceback").code(traceback.format_exc())

else:
    # --- ENHANCED LANDING PAGE ---
    st.title("AlphaStream | Quantitative Terminal")
    st.markdown("""
    Welcome to the AlphaStream Research Platform. This terminal implements an institutional-grade 
    quantitative strategy combining **Factor Research**, **Machine Learning**, and **Convex Optimization**.
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Strategy Overview")
        st.markdown("""
        - **Engine:** Ridge Regression with Walk-Forward Validation.
        - **Factors:** Momentum, Volatility, Quality (ROE).
        - **Optimization:** SciPy SLSQP Mean-Variance Optimization.
        - **Universe:** Liquid S&P 500 Constituents.
        """)
        
        st.info("💡 Adjust your constraints in the sidebar and click **EXECUTE BACKTEST** to generate out-of-sample results.")

    with col2:
        st.subheader("Market Context")
        # Show SPY as baseline
        with st.spinner("Loading market data..."):
            spy = yf.download('SPY', period='1y', progress=False)['Close']
            if isinstance(spy, pd.DataFrame): spy = spy.iloc[:, 0]
            fig_spy = px.line(spy, title="S&P 500 (SPY) Trailing 12M", labels={'value': 'Price', 'Date': ''})
            fig_spy.update_traces(line_color=COLORS['text_muted'])
            st.plotly_chart(apply_custom_theme(fig_spy), use_container_width=True)

    st.markdown("---")
    st.caption("AlphaStream Terminal v2.0 | Out-of-Sample Integrity Verified")
