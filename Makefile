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
WAVE01_PYTHONPATH := /usr/lib/python3/dist-packages:$(CURDIR)/packages/servicefabric_application_assembly:$(CURDIR)/packages/servicefabric_application_model:$(CURDIR)/packages/servicefabric_artifacts:$(CURDIR)/packages/servicefabric_blueprints:$(CURDIR)/packages/servicefabric_framework_kits:$(CURDIR)/packages/servicefabric_process_runtime:$(CURDIR)/packages/servicefabric_resource_bindings:$(CURDIR)/packages/servicefabric_workspace:$(CURDIR)/services/application_host:$(CURDIR)/clients/python
WAVE01_BIN ?= /tmp/servicefabric-ap-01a/bin
WAVE01_PATH := $(WAVE01_BIN):$(PATH)
WAVE01_PYTHON ?= /usr/bin/python3
WAVE01_ENV := env -u SERVICEFABRIC_WORKSPACE
WAVE02_PYTHON ?= $(WAVE01_BIN)/python
WAVE02_PYTHONPATH := /usr/lib/python3/dist-packages:$(WAVE01_PYTHONPATH):$(CURDIR)/services/application_dev_supervisor
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
verify-wave-01:
	$(WAVE01_PYTHON) scripts/agent/wave_completion.py --wave wave-1
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m unittest discover -s tests/application_assembly -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m unittest discover -s tests/resource_bindings -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m unittest discover -s tests/framework_kits -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m unittest discover -s tests/blueprints -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m unittest discover -s tests/integration -p 'test_wave_01_acceptance.py' -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m unittest discover -s tests/adversarial -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m unittest discover -s tests/architecture -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m unittest discover -s tests/modules -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m unittest discover -s packages/servicefabric_workspace/tests -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m unittest discover -s tests/workspace -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_BIN)/python -m unittest discover -s tests/ap_01a -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_BIN)/python -m unittest discover -s tests/local_ux -v
	$(WAVE01_PYTHON) scripts/dependencies/check_python_locks.py
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" python3 -m pip check
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE01_PYTHONPATH)" $(WAVE01_PYTHON) -m compileall packages/servicefabric_application_assembly packages/servicefabric_application_model packages/servicefabric_blueprints packages/servicefabric_framework_kits packages/servicefabric_process_runtime packages/servicefabric_resource_bindings packages/servicefabric_workspace services/application_host clients/python tests/application_assembly tests/resource_bindings tests/framework_kits tests/blueprints tests/integration tests/adversarial tests/architecture tests/modules tests/workspace tests/ap_01a tests/local_ux
	git diff --check
verify-wave-02:
	python3 -m unittest tests.agent.test_wave_harness tests.agent.test_wave_operational_scripts tests.agent.test_wave_rollover_scripts -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/wave_02 -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/application_dev_supervisor -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/resource_bindings -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/framework_kits -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/blueprints -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/application_assembly -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/integration -p 'test_wave_01_acceptance.py' -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/adversarial -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/modules -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s packages/servicefabric_workspace/tests -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/workspace -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/ap_01a -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/local_ux -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/architecture -v
	python3 scripts/dependencies/check_python_locks.py
	python3 -m pip check
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m compileall packages/servicefabric_application_assembly packages/servicefabric_application_model packages/servicefabric_blueprints packages/servicefabric_framework_kits packages/servicefabric_process_runtime packages/servicefabric_resource_bindings packages/servicefabric_workspace services/application_dev_supervisor services/application_host clients/python tests/wave_02 tests/application_dev_supervisor tests/application_assembly tests/resource_bindings tests/framework_kits tests/blueprints tests/integration tests/adversarial tests/architecture tests/modules tests/workspace tests/ap_01a tests/local_ux
	git diff --check
verify-application-workspace:
	python3 -m unittest discover -s packages/servicefabric_workspace/tests -v
	python3 -m unittest discover -s tests/workspace -v
	python3 -m unittest discover -s tests/modules -v
	python3 -m unittest discover -s tests/framework_kits -v
	python3 -m unittest tests.architecture.test_workspace_boundaries tests.architecture.test_legacy_application_paths -v
	python3 -m unittest discover -s tests/local_ux -v
	python3 -m unittest discover -s tests/ap_01a -v
	python3 scripts/dependencies/check_python_locks.py
	python3 -m pip check
	python3 -m compileall packages/servicefabric_workspace packages/servicefabric_application_model packages/servicefabric_framework_kits services/application_host clients/python tests/workspace tests/modules
	git diff --check
