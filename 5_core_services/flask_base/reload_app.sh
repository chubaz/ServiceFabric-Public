#!/bin/bash

# Service Fabric - Global App Reloader

APP_NAME=$1

if [ -z "$APP_NAME" ]; then
    echo "❌ Error: Please provide the application name as an argument."
    echo "Usage: ./reload_app.sh <app_name>"
    exit 1
fi

echo "🔄 Triggering Graceful Hot-Reload for the Fabric Core to pick up '$APP_NAME'..."

# Invia un segnale SIGHUP a Gunicorn (che in questo container è il processo principale con PID 1).
# Questo indica a Gunicorn di ricaricare tutto il codice Python in modo "morbido".
if kill -HUP 1; then
    echo "✅ Success: Reload signal sent to Gunicorn Master."
    echo "I worker si stanno riavviando senza far cadere le connessioni attive."
else
    echo "❌ Failed: Impossibile inviare il segnale di reload."
    exit 1
fi