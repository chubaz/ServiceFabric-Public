# 🚀 ServiceFabric

ServiceFabric is a modular, AI-ready microservices architecture featuring a Django core, FastAPI AI orchestration, and dynamic Vite/React frontend rendering. 

## ⚡ Quickstart (Under 3 Minutes)

We have fully automated the setup process. You do not need to configure databases, run migrations manually, or generate secret keys.

**1. Clone the repository:**

git clone https://github.com/chubaz/ServiceFabric.git

cd ServiceFabric

**2. Run the interactive setup:**

make setup

*The installer will ask you for a proxy port, database passwords, and admin credentials. It will then generate a secure `.env` file, boot the Docker network, and automatically run all database migrations.*

**3. Access the System:**
* Main Application: `http://localhost:[YOUR_PROXY_PORT]`
* Admin Panel: `http://localhost:[YOUR_PROXY_PORT]/admin`

---

## 🛠️ Daily Developer Workflow

This project uses a standard `Makefile` to manage the multi-container Docker environment easily.

* **`make dev`**: Boot the system in local development mode (live-reloading enabled).
* **`make prod`**: Boot the system using the production overrides.
* **`make down`**: Safely spin down all containers.
* **`make logs`**: View the live output of all running services.

## 📦 Backups & Teardown

To protect your generated applications and database state:
* **`make backup`**: Automatically dumps your PostgreSQL database and archives your `6_service_catalog` into the `8_backups/` directory.
* **`make teardown`**: Destroys all containers, wipes the database volumes, and cleans the generated apps directory (giving you a fresh slate).
