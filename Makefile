# Makefile for ServiceFabric operations

setup:
	chmod +x install.sh
	./install.sh

# Run local development without Cloudflare
dev:
	cp .env.example.dev .env
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Run production with Cloudflare
prod:
	cp .env.example.prod .env
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

up:
	docker compose -f docker-compose.dev.yml up -d

down:
	docker compose -f docker-compose.dev.yml down

logs:
	docker compose -f docker-compose.dev.yml logs -f

backup:
	docker exec -t db pg_dump -U postgres servicefabric > 8_backups/db_backup.sql
	tar -czf 8_backups/service_catalog_backup.tar.gz 6_service_catalog/

# Django Management Commands
migration: makemigrations migrate

makemigrations:
	docker compose exec backend_api python manage.py makemigrations

migrate:
	docker compose exec backend_api python manage.py migrate

collectstatic:
	docker compose exec backend_api python manage.py collectstatic --noinput

seed:
	docker compose exec backend_api python seed_templates.py

createsuperuser:
	docker compose exec backend_api python manage.py createsuperuser

teardown:
	docker compose down -v
	# Delete everything in 6_service_catalog except _shared and its content
	find 6_service_catalog/ -mindepth 1 -not -name "_shared" -not -path "6_service_catalog/_shared*" -delete
