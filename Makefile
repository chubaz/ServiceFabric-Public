# Makefile for ServiceFabric operations

setup:
	chmod +x install.sh
	./install.sh

# Run local development without Cloudflare
dev:
	@test -f .env.dev || cp .env.example.dev .env.dev
	SERVICEFABRIC_ENV_FILE=.env.dev docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Run production with Cloudflare
prod:
	@$(MAKE) prod-preflight
	SERVICEFABRIC_ENV_FILE=.env.prod docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-preflight:
	@test -f .env.prod || (echo "Refusing production start: create .env.prod from .env.example.prod and supply real secrets." >&2; exit 1)
	@python3 scripts/compose/validate_production_env.py .env.prod
	@SERVICEFABRIC_ENV_FILE=.env.prod docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml config >/dev/null

prod-migrate:
	@$(MAKE) prod-preflight
	SERVICEFABRIC_ENV_FILE=.env.prod docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml run --rm backend_api python manage.py migrate --noinput

prod-collectstatic:
	@$(MAKE) prod-preflight
	SERVICEFABRIC_ENV_FILE=.env.prod docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml run --rm backend_api python manage.py collectstatic --noinput

up:
	$(MAKE) dev

down:
	SERVICEFABRIC_ENV_FILE=.env.dev docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml down

logs:
	SERVICEFABRIC_ENV_FILE=.env.dev docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml logs -f

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

MILESTONE ?= $(shell python3 -c 'import json;print(json.load(open("docs/workplans/status.json"))["current_milestone"])')
agent-preflight:
	python3 scripts/agent/preflight.py --milestone $(MILESTONE)
agent-context:
	python3 scripts/agent/context.py --milestone $(MILESTONE)
agent-validate:
	python3 scripts/agent/validate_workplans.py
agent-verify:
	python3 scripts/agent/verify.py --milestone $(MILESTONE) --phase readiness
agent-report:
	python3 scripts/agent/completion_report.py --milestone $(MILESTONE)
agent-handoff:
	python3 scripts/agent/prepare_handoff.py --milestone $(MILESTONE)
verify-e0-00:
	python3 scripts/agent/verify.py --milestone e0-00 --phase completion
verify-current:
	python3 scripts/agent/verify.py --milestone $(MILESTONE) --phase readiness
verify-ap-01a-hosting:
	python3 -m unittest tests.ap_01a.test_hosting_baseline -v
verify-application-workspace:
	python3 -m unittest discover -s packages/servicefabric_workspace/tests -v
	python3 -m unittest discover -s tests/workspace -v
	python3 -m unittest tests.architecture.test_workspace_boundaries tests.architecture.test_legacy_application_paths -v
	python3 -m unittest discover -s tests/local_ux -v
	python3 -m unittest discover -s tests/ap_01a -v
	python3 scripts/dependencies/check_python_locks.py
	python3 -m pip check
	python3 -m compileall packages/servicefabric_workspace services/application_host clients/python tests/workspace
	git diff --check
