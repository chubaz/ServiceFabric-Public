#!/bin/bash

# ServiceFabric Unified Installer

echo "------------------------------------------------"
echo "   ServiceFabric Setup - Unified Installer      "
echo "------------------------------------------------"

# --- 1. User Inputs ---

# Track ports allocated during this session to avoid internal conflicts
ALLOCATED_PORTS=()

# Helper function to find a free port
find_free_port() {
    local port=$1
    # Check if port is in use using nc (NetCat) OR if it was already allocated in this script
    while nc -z localhost $port >/dev/null 2>&1 || [[ " ${ALLOCATED_PORTS[*]} " == *" $port "* ]]; do
        port=$((port + 1))
    done
    echo $port
}

# Proxy Configuration
suggested_proxy_port=$(find_free_port 8080)
read -p "Enter Proxy Port (suggested $suggested_proxy_port): " PROXY_PORT
PROXY_PORT=${PROXY_PORT:-$suggested_proxy_port}

# Check if the chosen PROXY_PORT is actually free, if not, find another one
FINAL_PROXY_PORT=$(find_free_port $PROXY_PORT)
if [ "$FINAL_PROXY_PORT" != "$PROXY_PORT" ]; then
    echo "Port $PROXY_PORT is in use. Using $FINAL_PROXY_PORT instead."
    PROXY_PORT=$FINAL_PROXY_PORT
fi
ALLOCATED_PORTS+=($PROXY_PORT)

# Allocate other service ports automatically
FASTAPI_PORT=$(find_free_port 8081)
ALLOCATED_PORTS+=($FASTAPI_PORT)

BACKEND_API_PORT=$(find_free_port 8002)
ALLOCATED_PORTS+=($BACKEND_API_PORT)

VITE_PORT=$(find_free_port 5173)
ALLOCATED_PORTS+=($VITE_PORT)

echo "Allocated ports:"
echo "  - Proxy: $PROXY_PORT"
echo "  - FastAPI: $FASTAPI_PORT"
echo "  - Backend API: $BACKEND_API_PORT"
echo "  - Vite (Component Lab): $VITE_PORT"

# Database Configuration
read -p "Enter Database Name (default servicefabric): " POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-servicefabric}

read -p "Enter Database User (default devAdmin): " POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-devAdmin}

read -s -p "Enter Database Password: " POSTGRES_PASSWORD
echo ""

# Superuser Configuration
read -p "Enter Superuser Name (default admin): " SUPERUSER_NAME
SUPERUSER_NAME=${SUPERUSER_NAME:-admin}

read -p "Enter Superuser Email: " SUPERUSER_EMAIL

read -s -p "Enter Superuser Password: " SUPERUSER_PASSWORD
echo ""

# API Keys (Optional)
read -p "Enter Gemini API Key (optional): " GEMINI_API_KEY
read -p "Enter OpenAI API Key (optional): " OPENAI_API_KEY
read -p "Enter Mistral API Key (optional): " MISTRAL_API_KEY

# Environment Selection
read -p "Is this a development environment? (y/n, default y): " IS_DEV
IS_DEV=${IS_DEV:-y}

# --- Isolation naming ---
# Get current directory name and sanitize it (lowercase, remove non-alphanumeric)
CURRENT_DIR=$(basename "$PWD")
DIR_NAME_SANITIZED=$(echo "$CURRENT_DIR" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')

if [ "$IS_DEV" = "y" ]; then
    DEBUG=1
    ALLOWED_HOSTS="localhost, 127.0.0.1"
    DEFAULT_PROJECT_NAME="sf_dev_${DIR_NAME_SANITIZED}"
else
    DEBUG=0
    read -p "Enter Allowed Hosts (comma separated): " ALLOWED_HOSTS
    DEFAULT_PROJECT_NAME="sf_prod_${DIR_NAME_SANITIZED}"
fi

read -p "Enter Compose Project Name (default $DEFAULT_PROJECT_NAME): " CUSTOM_PROJECT_NAME
COMPOSE_PROJECT_NAME=${CUSTOM_PROJECT_NAME:-$DEFAULT_PROJECT_NAME}
echo "Using project name: $COMPOSE_PROJECT_NAME"

# --- 2. Automatic Generation ---

# Generate Secret Keys
SECRET_KEY=$(openssl rand -hex 50)
DJANGO_SECRET_KEY=$SECRET_KEY

# Construct Database URL
DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB"

# Static Paths
SERVICE_CATALOG_PATH="/app/services_catalog"
STATIC_ASSETS_PATH="/app/flask_static"

# Internal Service URLs
FLASK_SERVICE_URL="http://core_flask_service:5000"
DJANGO_SERVICE_URL="http://backend_api:8000"
REDIS_URL="redis://redis:6379/0"

# --- 3. Create Consolidated .env ---

if [ "$IS_DEV" = "y" ]; then
    ENV_TARGET=".env.dev"
else
    ENV_TARGET=".env.prod"
fi

echo "Creating consolidated $ENV_TARGET file..."
cat <<EOF > $ENV_TARGET
# --- Core Config ---
COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT_NAME
PROXY_PORT=$PROXY_PORT
FASTAPI_PORT=$FASTAPI_PORT
BACKEND_API_PORT=$BACKEND_API_PORT
VITE_PORT=$VITE_PORT
DEBUG=$DEBUG
ALLOWED_HOSTS=$ALLOWED_HOSTS

# --- Django Config ---
SECRET_KEY=$SECRET_KEY
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY

# --- Database Config ---
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
DATABASE_URL=$DATABASE_URL

# --- Superuser Config ---
DJANGO_SUPERUSER_USERNAME=$SUPERUSER_NAME
DJANGO_SUPERUSER_EMAIL=$SUPERUSER_EMAIL
DJANGO_SUPERUSER_PASSWORD=$SUPERUSER_PASSWORD

# --- Paths & Services ---
SERVICE_CATALOG_PATH=$SERVICE_CATALOG_PATH
STATIC_ASSETS_PATH=$STATIC_ASSETS_PATH
FLASK_SERVICE_URL=$FLASK_SERVICE_URL
DJANGO_SERVICE_URL=$DJANGO_SERVICE_URL
REDIS_URL=$REDIS_URL

# --- AI API Keys ---
GEMINI_API_KEY=$GEMINI_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
VITE_GEMINI_API_KEY=$GEMINI_API_KEY
MISTRAL_API_KEY=$MISTRAL_API_KEY
EOF

# Ensure .env also exists as a backup/default for other tools
cp $ENV_TARGET .env

echo "$ENV_TARGET and .env files created."

# --- 4. Execution ---

echo "Building and starting containers..."
if [ "$IS_DEV" = "y" ]; then
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
else
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
fi

# We use --build to ensure any changes in Dockerfiles are picked up
docker compose $COMPOSE_FILES up -d --build

echo "Waiting for services to initialize..."
# The container entrypoint handles migrations, static files, and seeding.
# We just wait a bit to let it finish its startup sequence.
sleep 10

echo "------------------------------------------------"
echo "   Setup Complete! Service is running on port $PROXY_PORT"
echo "------------------------------------------------"
