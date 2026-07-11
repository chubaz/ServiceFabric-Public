FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl libpq-dev && \
    rm -rf /var/lib/apt/lists/*
COPY 5_core_services/flask_base/requirements ./requirements
RUN pip install --no-cache-dir -r requirements/runtime.lock && \
    useradd --create-home --uid 10001 appuser

# The catalogue is a build-time snapshot. Production never mounts mutable source.
COPY --chown=appuser:appuser 5_core_services/flask_base /app/
COPY --chown=appuser:appuser 6_service_catalog /app/services_catalog
RUN mkdir -p /app/user_media /app/flask_static /app/shared && \
    chown -R appuser:appuser /app

USER appuser
EXPOSE 5000
CMD ["gunicorn", "-w", "1", "--threads", "4", "--bind", "0.0.0.0:5000", "--timeout", "60", "--graceful-timeout", "30", "--log-level", "info", "run:app"]
