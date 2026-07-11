import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def audit_log_event(app_name: str, event_type: str, payload: dict):
    """
    A simulated heavy background task (e.g., saving to a data warehouse).
    """
    logger.info(f"Started auditing event '{event_type}' for app '{app_name}'...")
    # Simulate I/O bound wait time (like saving to a slow database)
    await asyncio.sleep(3) 
    logger.info(f"Successfully saved audit log for {app_name}: {payload}")
