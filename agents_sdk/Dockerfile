FROM python:3.11-slim

WORKDIR /agents_sdk

# Install git (needed for code_review git diff) and curl
RUN apt-get update && apt-get install -y --no-install-recommends git curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --retries 10 -r requirements.txt

# The actual source is mounted at runtime (see docker-compose)
CMD ["python", "scheduler.py"]
