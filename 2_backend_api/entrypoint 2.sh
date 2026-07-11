#!/bin/sh
# /service-fabric-project/2_backend_api/entrypoint.sh

# 1. Attendiamo che il Database (chiamato 'db', come da docker-compose)
#    sia pronto ad accettare connessioni sulla porta 5432.
#    (Questo richiede l'installazione di 'netcat' nel Dockerfile)
# ripete il test fino a che la connessione nc (che non si ferma fino alla chiusura del network)
# non è attiva.
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# 2. Applichiamo le migrazioni del database Django
#    (Crea le tabelle T3: User, ServiceInstance, etc.)
echo "Applying database migrations..."
python manage.py migrate

# echo "Creating markdown editor service..."
# python service_fabric/create_markdown_service.py

# 3. Raccogliamo tutti i file statici (CSS, JS, e la nostra 'main.html')
#    e li copiamo nel volume condiviso 'static_volume' (/app/static).
#    Nginx (T1) leggerà da questo volume per servire il frontend.
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 4. Avviamo il server di produzione Gunicorn.
#    NON usiamo 'manage.py runserver' (come nel tuo 'run.py'),
#    che è solo per lo sviluppo.
echo "Starting Gunicorn..."
gunicorn myproject.wsgi:application --bind 0.0.0.0:8000