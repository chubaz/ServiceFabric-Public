import os
import time
import requests
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer

# --- CONFIGURATION ---
FLASK_URL = os.environ.get("FLASK_URL", "http://core_flask_service:5000/_internal/reload")
VITE_URL = os.environ.get("VITE_URL", "http://core_vite_service:3000/_internal/reload")
REACT_URL = os.environ.get("REACT_URL", "http://core_react_service:3000/_internal/reload")

WATCH_DIR = "/services_catalog"
DEBOUNCE_SECONDS = 1.0 # Increased debounce for stability
WATCHER_RELOAD_ENABLED = os.environ.get("ENABLE_WATCHER_RELOAD", "false").lower() in {"1", "true", "yes", "on"}
WATCHER_SERVICE_ID = os.environ.get("WATCHER_SERVICE_ID", "fabric_watcher")
WATCHER_RELOAD_TOKEN = os.environ.get("INTERNAL_RELOAD_TOKEN")

# Noisy paths to ignore completely
IGNORE_PATTERNS = [
    "__pycache__", ".git", ".pytest_cache", ".venv", "node_modules", 
    "dist", ".tmp", ".old", ".svelte-kit", ".DS_Store", ".vite", "vite.config.ts.timestamp"
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FabricWatcher")

class ShardEvent:
    def __init__(self, shard_name, service_type):
        self.shard_name = shard_name
        self.service_type = service_type
    def __hash__(self): return hash((self.shard_name, self.service_type))
    def __eq__(self, other): return self.shard_name == other.shard_name and self.service_type == other.service_type

class FabricHandler(FileSystemEventHandler):
    def __init__(self):
        self.pending_events = set()
        self.timer = None

    def on_modified(self, event): self.process_event(event.src_path)
    def on_created(self, event): self.process_event(event.src_path)
    def on_deleted(self, event): self.process_event(event.src_path)

    def process_event(self, path):
        # 1. Quick Ignore check
        if any(pattern in path for pattern in IGNORE_PATTERNS):
            return

        rel_path = os.path.relpath(path, WATCH_DIR)
        parts = rel_path.split(os.sep)
        
        if len(parts) < 2: return 

        shard_name = parts[0]
        if shard_name.startswith(('.', '_')): return

        service_type = self.detect_service_type(shard_name, path)
        if not service_type: return

        event = ShardEvent(shard_name, service_type)
        self.pending_events.add(event)
        
        if self.timer: self.timer.cancel()
        self.timer = Timer(DEBOUNCE_SECONDS, self.dispatch_events)
        self.timer.start()

    def detect_service_type(self, shard_name, file_path):
        # Priority markers
        if file_path.endswith('.py'): return "FLASK"
        
        shard_root = os.path.join(WATCH_DIR, shard_name)
        if os.path.exists(os.path.join(shard_root, "src", "main.tsx")): return "REACT"
        if os.path.exists(os.path.join(shard_root, "src", "main.ts")): return "VITE"
        
        # Extensions fallback
        if file_path.endswith(('.tsx', '.jsx')): return "REACT"
        if file_path.endswith(('.ts', '.svelte')): return "VITE"
        return None

    def dispatch_events(self):
        events_to_process = list(self.pending_events)
        self.pending_events.clear()
        for event in events_to_process:
            self.trigger_reload(event)

    def trigger_reload(self, event):
        if not WATCHER_RELOAD_ENABLED:
            logger.info("Reload notifications are disabled")
            return
        if not WATCHER_RELOAD_TOKEN:
            logger.warning("Reload skipped because watcher credentials are not configured")
            return
        url = {"FLASK": FLASK_URL, "REACT": REACT_URL, "VITE": VITE_URL}.get(event.service_type)
        if not url: return

        logger.info(f"🔄 Triggering {event.service_type} reload: {event.shard_name}")
        try:
            # Short timeout to avoid hanging the watcher
            headers = {
                "X-Service-Identity": WATCHER_SERVICE_ID,
                "X-Internal-Reload-Token": WATCHER_RELOAD_TOKEN,
            }
            requests.post(url, json={"target": event.shard_name}, headers=headers, timeout=2)
        except Exception as e:
            logger.error(f"❌ Target {event.service_type} unreachable: {e}")

if __name__ == "__main__":
    logger.info(f"🏭 Fabric Watcher v1.1 Active (Safe Mode)")
    event_handler = FabricHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=True)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
