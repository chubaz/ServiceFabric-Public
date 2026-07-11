import logging
import time
import random
from _shared.utils.fabric_sdk import fabric

def ingest_market_data(tickers=["AAPL", "MSFT", "GOOGL"]):
    """
    Task: Ingest daily close prices from external APIs.
    """
    logger = logging.getLogger("fabric.quant.ingestion")
    logger.info(f"Starting ingestion for {{APP_SLUG}}: {tickers}")
    try:
        logger.info("Ingestion simulated successfully.")
        return True
    except Exception as e:
        logger.error(f"Ingestion failed for {{APP_SLUG}}: {e}")
        return False

def broadcast_live_pnl(initial_capital: float = 100000.0):
    """
    Background worker that simulates live PnL updates.
    Broadcasts 'portfolio_pnl_update' events to the central Fabric Gateway.
    """
    app_slug = "{{APP_SLUG}}"
    current_value = initial_capital
    
    while True:
        # Simulate a market tick (e.g., +/- 0.5%)
        tick_return = random.uniform(-0.005, 0.005)
        current_value = current_value * (1 + tick_return)
        
        pnl_data = {
            "slug": app_slug,
            "timestamp": time.time(),
            "total_value": round(current_value, 2),
            "daily_pnl_perc": round(tick_return * 100, 3)
        }
        
        # Push payload to the centralized Fabric Gateway
        fabric.broadcast("portfolio_pnl_update", pnl_data)
        
        # Wait for the next tick (5 seconds)
        time.sleep(5)
