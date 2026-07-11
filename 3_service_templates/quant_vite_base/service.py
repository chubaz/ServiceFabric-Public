import numpy as np
try:
    import polars as pl
except ImportError:
    import pandas as pl # Fallback if polars not in env
from .models import {{APP_SLUG}}Entity

class ServiceRunner:
    """
    Quant-Fabric Engine: High-performance financial logic.
    Optimized for execution within the Service Fabric FaaS window.
    """
    def __init__(self, context):
        self.user_id = context.get('user_id')
        self.config = context.get('config', {})
        self.logger = context.get('logger')

    def run(self, input_data):
        """
        Main execution entry point for Alpha-factor generation or backtesting.
        """
        try:
            # Example: Vectorized calculation using NumPy
            prices = np.array(input_data.get('prices', [100, 101, 102]))
            returns = np.diff(prices) / prices[:-1]
            
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 0 else 0
            
            return {
                "status": "success",
                "sharpe_ratio": float(sharpe),
                "msg": f"Engine {{APP_SLUG}} processed {len(prices)} ticks."
            }
        except Exception as e:
            if self.logger: self.logger.error(f"Quant Engine Error in {{APP_SLUG}}: {e}")
            raise e
