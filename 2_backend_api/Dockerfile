FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser ./service_fabric /app/
COPY --chown=appuser:appuser entrypoint.sh /entrypoint.sh
RUN chmod 0555 /entrypoint.sh && mkdir -p /app/static && chown appuser:appuser /app/static

USER appuser
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
