# 1. Usa un'immagine base ufficiale Python leggera
FROM python:3.11-slim

# 2. Imposta variabili d'ambiente per l'ottimizzazione Python
# Evita la creazione di file .pyc (inutile in container) e forza i log su stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Imposta la directory di lavoro
WORKDIR /app

# 4. Installa dipendenze di sistema necessarie
# libpq-dev e gcc servono per compilare psycopg2 (driver Postgres)
# curl è utile per gli healthcheck
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Gestione Dipendenze Python (Layer Caching)
# Copiamo prima solo il requirements.txt per sfruttare la cache di Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 --retries 10 -r requirements.txt

# 6. Copia il codice sorgente dell'applicazione
COPY . .

# 7. Creazione utente non-root per sicurezza
# Non eseguiamo mai l'applicazione come root in produzione
RUN adduser --disabled-password --gecos '' appuser

# Creiamo le directory per i volumi (Catalogo e Media) e assegniamo i permessi
# Questo è fondamentale perché questi volumi verranno montati dall'host
RUN mkdir -p /app/services_catalog /app/user_media && \
    chown -R appuser:appuser /app/services_catalog /app/user_media

# Passiamo all'utente sicuro
USER appuser

# 8. Espone la porta definita nel docker-compose (5000)
EXPOSE 5000

# 9. Comando di avvio (Produzione)
# Usiamo il worker standard (sync) poiché i WebSockets sono gestiti dal Gateway FastAPI
CMD ["gunicorn", "-w", "1", "--threads", "4", "--bind", "0.0.0.0:5000", "--timeout", "300", "--log-level", "info", "run:app"]