FROM python:3.11.9-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements/runtime.lock
RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/user_media && chown -R appuser:appuser /app
COPY --chown=appuser:appuser ./app ./app
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "30"]
