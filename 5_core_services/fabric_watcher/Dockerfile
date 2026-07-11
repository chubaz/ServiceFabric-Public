# 1. Base Image
FROM python:3.11-slim

# 2. Environment Setup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 3. Dependencies
# watchdog needs no system-level libraries but requests does for SSL (though we hit local containers)
COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements/runtime.lock

# 4. Source
COPY watcher.py .

# 5. Security (Non-root)
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# 6. Command
# We'll point to /services_catalog as our watch root
CMD ["python", "watcher.py"]
