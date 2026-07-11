# /service-fabric-project/2_backend_api/Dockerfile

# 1. Partiamo da un'immagine Python ufficiale e "slim"
FROM python:3.11-slim

# Aggiorna gli indici dei pacchetti
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# 2. Impostiamo variabili d'ambiente standard per Python (standard per I/O connessioni senza buffer) // flush immediato
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Creiamo una directory di lavoro all'interno del container
WORKDIR /app

# 4. Copiamo *solo* il file requirements.txt
COPY requirements.txt .

# 5. Installiamo le dipendenze.
#    Docker memorizza questo strato. Se 'requirements.txt' non cambia,
#    Docker salterà questo passo, velocizzando le build future.
RUN pip install --no-cache-dir --default-timeout=100 --retries 10 -r requirements.txt

# 6. Copiamo lo script di avvio e lo rendiamo eseguibile // standard bash to copy shell script and making it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 7. Copiamo *tutto* il nostro codice sorgente Django // create the Django app source code in Docker
#    (la cartella 'service_fabric') nella directory di lavoro
COPY ./service_fabric /app/

# 8. Esponiamo la porta 8000 (per Gunicorn) alla rete interna // container opening which will be exposed to the Docker network
#    (Nginx si collegherà a questa porta)
EXPOSE 8000

# Trigger rebuild
# 9. Il comando finale per avviare il container.
#    Non esegue Django direttamente, ma avvia lo script 'entrypoint.sh'.
CMD ["/entrypoint.sh"]

