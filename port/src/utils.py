# src/utils.py
import time
import logging
from functools import wraps

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def timeit(func):
    """
    A decorator that logs the execution time of a function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logging.info(f"⏱️ STARTED: {func.__name__}")
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"✅ FINISHED: {func.__name__} in {elapsed_time:.2f} seconds")
        
        return result
    return wrapper