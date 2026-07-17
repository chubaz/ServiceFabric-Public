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
WAVE01_PYTHONPATH := /usr/lib/python3/dist-packages:$(CURDIR):$(CURDIR)/packages/servicefabric_application_assembly:$(CURDIR)/packages/servicefabric_application_model:$(CURDIR)/packages/servicefabric_artifacts:$(CURDIR)/packages/servicefabric_blueprints:$(CURDIR)/packages/servicefabric_capability_authoring:$(CURDIR)/packages/servicefabric_framework_kits:$(CURDIR)/packages/servicefabric_process_runtime:$(CURDIR)/packages/servicefabric_resource_bindings:$(CURDIR)/packages/servicefabric_workspace:$(CURDIR)/services/application_host:$(CURDIR)/clients/python
WAVE01_BIN ?= /tmp/servicefabric-ap-01a/bin
WAVE01_PATH := $(WAVE01_BIN):$(PATH)
WAVE01_PYTHON ?= /usr/bin/python3
WAVE01_ENV := env -u SERVICEFABRIC_WORKSPACE -u SERVICEFABRIC_HOME
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

WAVE3_PYTHON ?= $(WAVE01_BIN)/python
WAVE3_PYTHONPATH := /usr/lib/python3/dist-packages:$(CURDIR):$(CURDIR)/services/application_dev_supervisor:$(CURDIR)/services/application_host:$(CURDIR)/services/capsule_host:$(CURDIR)/services/governance_operations:$(CURDIR)/services/mcp_gateway:$(CURDIR)/services/tool_runtime:$(CURDIR)/clients/python:$(CURDIR)/packages/servicefabric_application_generator:$(CURDIR)/packages/servicefabric_application_builder:$(CURDIR)/packages/servicefabric_agent_guidance:$(CURDIR)/packages/servicefabric_application_model:$(CURDIR)/packages/servicefabric_application_assembly:$(CURDIR)/packages/servicefabric_artifacts:$(CURDIR)/packages/servicefabric_blueprints:$(CURDIR)/packages/servicefabric_capability_authoring:$(CURDIR)/packages/servicefabric_builder:$(CURDIR)/packages/servicefabric_capsules/src:$(CURDIR)/packages/servicefabric_contracts/src:$(CURDIR)/packages/servicefabric_framework_kits:$(CURDIR)/packages/servicefabric_governance/src:$(CURDIR)/packages/servicefabric_mcp_projection/src:$(CURDIR)/packages/servicefabric_operations/src:$(CURDIR)/packages/servicefabric_process_runtime:$(CURDIR)/packages/servicefabric_resource_bindings:$(CURDIR)/packages/servicefabric_runtime:$(CURDIR)/packages/servicefabric_workspace
WAVE3_ENV := env -u SERVICEFABRIC_WORKSPACE PATH="$(dir $(WAVE3_PYTHON)):$(PATH)" PYTHONPATH="$(WAVE3_PYTHONPATH)"

verify-wave-03:
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/wave_03 -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/application_generator -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/application_builder -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/agent_guidance -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/blueprints -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) scripts/agent/wave_completion.py --wave wave-01
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/application_assembly -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/resource_bindings -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/framework_kits -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/blueprints -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/integration -p 'test_wave_01_acceptance.py' -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/adversarial -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/architecture -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/modules -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s packages/servicefabric_workspace/tests -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/local_ux -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/ap_01a -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s packages/servicefabric_workspace/tests -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/workspace -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m unittest discover -s tests/modules -v
	$(WAVE3_ENV) $(WAVE3_PYTHON) scripts/dependencies/check_python_locks.py
	env -u SERVICEFABRIC_WORKSPACE -u PYTHONPATH PATH="$(dir $(WAVE3_PYTHON)):$(PATH)" $(WAVE3_PYTHON) -m pip check
	$(WAVE3_ENV) $(WAVE3_PYTHON) -m compileall packages/servicefabric_application_generator packages/servicefabric_application_builder packages/servicefabric_agent_guidance packages/servicefabric_application_model packages/servicefabric_application_assembly packages/servicefabric_blueprints packages/servicefabric_framework_kits packages/servicefabric_artifacts packages/servicefabric_workspace packages/servicefabric_process_runtime clients/python services/application_host tests/wave_03 tests/application_generator tests/application_builder tests/agent_guidance tests/blueprints tests/ap_01a tests/workspace tests/modules
verify-wave-02:
	# Keep the wave gate focused; milestone-wide regressions are owned by verify-current.
	python3 -m unittest tests.agent.test_wave_harness tests.agent.test_wave_operational_scripts tests.agent.test_wave_rollover_scripts -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/wave_02 -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/application_dev_supervisor -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/resource_bindings -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/framework_kits -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/blueprints -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/application_assembly -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/integration -p 'test_wave_01_acceptance.py' -v
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m unittest discover -s tests/adversarial -v
	python3 scripts/dependencies/check_python_locks.py
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" python3 -m pip check
	$(WAVE01_ENV) PATH="$(WAVE01_PATH)" PYTHONPATH="$(WAVE02_PYTHONPATH)" $(WAVE02_PYTHON) -m compileall clients/python/servicefabric_client/development.py clients/python/servicefabric_client/static_web_server.py clients/python/servicefabric_client/main.py services/application_dev_supervisor tests/wave_02
	git diff --check

WAVE04_PYTHON ?= $(WAVE02_PYTHON)
WAVE04_PYTHONPATH := $(WAVE3_PYTHONPATH):$(CURDIR)/packages/servicefabric_operation_model:$(CURDIR)/packages/servicefabric_capability_model/src:$(CURDIR)/packages/servicefabric_capability_registry/src
WAVE04_ENV := env -u SERVICEFABRIC_WORKSPACE -u SERVICEFABRIC_HOME PATH="$(dir $(WAVE04_PYTHON)):$(PATH)" PYTHONPATH="$(WAVE04_PYTHONPATH)"

verify-wave-04:
	$(MAKE) verify-wave-01
	$(MAKE) verify-wave-02
	$(MAKE) verify-wave-03
	$(WAVE04_ENV) $(WAVE04_PYTHON) -m unittest discover -s tests/operation_model -v
	$(WAVE04_ENV) $(WAVE04_PYTHON) -m unittest discover -s tests/capability_model -v
	$(WAVE04_ENV) $(WAVE04_PYTHON) -m unittest discover -s tests/capability_registry -v
	$(WAVE04_ENV) $(WAVE04_PYTHON) -m unittest discover -s tests/capability_authoring -v
	$(WAVE04_ENV) $(WAVE04_PYTHON) -m unittest discover -s tests/wave_04 -v
	$(WAVE04_ENV) $(WAVE04_PYTHON) -m unittest discover -s tests/blueprints -v
	$(WAVE04_ENV) $(WAVE04_PYTHON) -m unittest discover -s tests/application_generator -v
	$(WAVE04_ENV) $(WAVE04_PYTHON) scripts/dependencies/check_python_locks.py
	env -u SERVICEFABRIC_WORKSPACE -u SERVICEFABRIC_HOME -u PYTHONPATH PATH="$(dir $(WAVE04_PYTHON)):$(PATH)" $(WAVE04_PYTHON) -m pip check
	$(WAVE04_ENV) $(WAVE04_PYTHON) -m compileall clients/python/servicefabric_client packages/servicefabric_operation_model packages/servicefabric_capability_model packages/servicefabric_capability_registry packages/servicefabric_capability_authoring tests/wave_04
	git diff --check

WAVE05_PYTHON ?= $(WAVE04_PYTHON)
WAVE05_PYTHONPATH := $(WAVE04_PYTHONPATH):$(CURDIR)/packages/servicefabric_capability_runtime:$(CURDIR)/packages/servicefabric_capability_runtime/src:$(CURDIR)/packages/servicefabric_capability_invocation:$(CURDIR)/packages/servicefabric_capability_invocation/src:$(CURDIR)/packages/servicefabric_http_operation_adapter:$(CURDIR)/packages/servicefabric_http_operation_adapter/src
WAVE05_ENV := env -u SERVICEFABRIC_WORKSPACE -u SERVICEFABRIC_HOME PATH="$(dir $(WAVE05_PYTHON)):$(PATH)" PYTHONPATH="$(WAVE05_PYTHONPATH)"

verify-wave-05:
	# Wave-5 is intentionally focused; do not recursively invoke earlier wave gates.
	$(WAVE05_ENV) $(WAVE05_PYTHON) -m unittest discover -s tests/capability_runtime -v
	$(WAVE05_ENV) $(WAVE05_PYTHON) -m unittest discover -s tests/capability_invocation -v
	$(WAVE05_ENV) $(WAVE05_PYTHON) -m unittest discover -s tests/http_operation_adapter -v
	$(WAVE05_ENV) $(WAVE05_PYTHON) -m unittest discover -s tests/wave_05 -v
	$(WAVE05_ENV) $(WAVE05_PYTHON) -m unittest tests.wave_04.test_capability_cli.CapabilityCliAcceptanceTests.test_registration_is_idempotent_and_listing_and_describe_are_deterministic -v
	$(WAVE05_ENV) $(WAVE05_PYTHON) -m unittest tests.adversarial.test_process_runtime_adversarial.ProcessRuntimeAdversarialTests.test_loopback_port_allocator_never_binds_wildcard_interface -v
	$(WAVE05_ENV) $(WAVE05_PYTHON) scripts/dependencies/check_python_locks.py
	env -u SERVICEFABRIC_WORKSPACE -u SERVICEFABRIC_HOME -u PYTHONPATH PATH="$(dir $(WAVE05_PYTHON)):$(PATH)" $(WAVE05_PYTHON) -m pip check
	$(WAVE05_ENV) $(WAVE05_PYTHON) -m compileall packages/servicefabric_capability_runtime packages/servicefabric_capability_invocation packages/servicefabric_http_operation_adapter
	git diff --check

WAVE06_PYTHON ?= $(WAVE05_PYTHON)
WAVE06_PYTHONPATH := $(WAVE05_PYTHONPATH):$(CURDIR)/packages/servicefabric_capability_mcp_projection/src:$(CURDIR)/packages/servicefabric_capability_consumers/src:$(CURDIR)/services/capability_rest_gateway/src:$(CURDIR)/services/mcp_gateway/src:$(CURDIR)/clients/python
WAVE06_ENV := env -u SERVICEFABRIC_WORKSPACE -u SERVICEFABRIC_HOME PATH="$(dir $(WAVE06_PYTHON)):$(PATH)" PYTHONPATH="$(WAVE06_PYTHONPATH)"

WAVE07_PYTHON ?= $(WAVE06_PYTHON)
WAVE07_PYTHONPATH := $(WAVE06_PYTHONPATH):$(CURDIR)/packages/servicefabric_agentic_contracts/src:$(CURDIR)/packages/servicefabric_agentic_context/src:$(CURDIR)/packages/servicefabric_agentic_planner/src:$(CURDIR)/packages/servicefabric_agentic_run_store/src:$(CURDIR)/packages/servicefabric_agent_tools/src:$(CURDIR)/packages/servicefabric_agentic_orchestrator/src:$(CURDIR)/packages/servicefabric_agent_harness/src
WAVE07_ENV := env -u SERVICEFABRIC_WORKSPACE -u SERVICEFABRIC_HOME PATH="$(dir $(WAVE07_PYTHON)):$(PATH)" PYTHONPATH="$(WAVE07_PYTHONPATH)"
WAVE08_PYTHON ?= $(WAVE07_PYTHON)
WAVE08_PYTHONPATH := $(WAVE07_PYTHONPATH):$(CURDIR)/packages/servicefabric_agent_provider_contracts/src:$(CURDIR)/packages/servicefabric_agent_provider_runtime/src:$(CURDIR)/packages/servicefabric_langgraph_orchestration/src:$(CURDIR)/packages/servicefabric_pi_harness/src:$(CURDIR)/packages/servicefabric_codex_adapter/src:$(CURDIR)/packages/servicefabric_claude_code_adapter/src:$(CURDIR)/packages/servicefabric_gemini_cli_adapter/src:$(CURDIR)/clients/python
WAVE08_ENV := env -u SERVICEFABRIC_WORKSPACE -u SERVICEFABRIC_HOME PATH="$(dir $(WAVE08_PYTHON)):$(PATH)" PYTHONPATH="$(WAVE08_PYTHONPATH)"

verify-wave-07:
	$(WAVE07_ENV) $(WAVE07_PYTHON) integration/phase25-wave7/verify_boundaries.py
	$(WAVE07_ENV) $(WAVE07_PYTHON) -m unittest discover -s tests/agentic_contracts -v
	$(WAVE07_ENV) $(WAVE07_PYTHON) -m unittest discover -s tests/agentic_context -v
	$(WAVE07_ENV) $(WAVE07_PYTHON) -m unittest discover -s tests/agentic_planner -v
	$(WAVE07_ENV) $(WAVE07_PYTHON) -m unittest discover -s tests/agentic_run_store -v
	$(WAVE07_ENV) $(WAVE07_PYTHON) -m unittest discover -s tests/agent_tools -v
	$(WAVE07_ENV) $(WAVE07_PYTHON) -m unittest discover -s tests/agentic_orchestrator -v
	$(WAVE07_ENV) $(WAVE07_PYTHON) -m unittest discover -s tests/agent_harness -v
	$(WAVE07_ENV) $(WAVE07_PYTHON) -m unittest discover -s tests/wave_07 -v
	$(WAVE07_ENV) $(WAVE07_PYTHON) -m unittest discover -s integration/phase25-wave7 -p 'test_*.py' -v
	git diff --check

verify-wave-08:
	$(WAVE08_ENV) $(WAVE08_PYTHON) integration/phase25-wave8/verify_boundaries.py
	$(WAVE08_ENV) $(WAVE08_PYTHON) -m unittest discover -s tests/agent_provider_contracts -v
	@for suite in tests/agent_provider_runtime tests/langgraph_orchestration tests/pi_harness tests/codex_adapter tests/claude_code_adapter tests/gemini_cli_adapter; do \
		if [ -d $$suite ]; then $(WAVE08_ENV) $(WAVE08_PYTHON) -m unittest discover -s $$suite -v; else echo "Wave-8 specialist suite pending: $$suite"; fi; \
	done
	$(WAVE08_ENV) $(WAVE08_PYTHON) -m unittest discover -s tests/wave_08 -v
	$(WAVE07_ENV) $(WAVE07_PYTHON) -m unittest tests.wave_07.test_framework_journey -v
	$(WAVE08_ENV) $(WAVE08_PYTHON) scripts/dependencies/check_python_locks.py
	env -u SERVICEFABRIC_WORKSPACE -u SERVICEFABRIC_HOME -u PYTHONPATH PATH="$(dir $(WAVE08_PYTHON)):$(PATH)" $(WAVE08_PYTHON) -m pip check
	$(WAVE08_ENV) $(WAVE08_PYTHON) -m compileall packages/servicefabric_agent_provider_contracts clients/python/servicefabric_client/agent_providers.py integration/phase25-wave8 tests/agent_provider_contracts tests/wave_08
	git diff --check

verify-wave-06:
	# Wave-6 is intentionally focused; projection lanes own their package suites.
	$(WAVE06_ENV) $(WAVE06_PYTHON) -m unittest discover -s tests/capability_mcp_projection -v
	$(WAVE06_ENV) $(WAVE06_PYTHON) -m unittest discover -s tests/capability_rest_gateway -v
	$(WAVE06_ENV) $(WAVE06_PYTHON) -m unittest discover -s tests/capability_consumers -v
	$(WAVE06_ENV) $(WAVE06_PYTHON) -m unittest discover -s tests/wave_06 -v
	$(WAVE06_ENV) $(WAVE06_PYTHON) -m unittest tests.wave_05.test_research_notes_acceptance.ResearchNotesCapabilityJourneyTests.test_registered_capabilities_follow_the_running_application_lifecycle -v
	$(WAVE06_ENV) $(WAVE06_PYTHON) -m unittest tests.mcp_projection.test_discovery.DiscoveryTests.test_disabled_unavailable_and_unauthorized_tools_remain_hidden -v
	$(WAVE06_ENV) $(WAVE06_PYTHON) scripts/dependencies/check_python_locks.py
	env -u SERVICEFABRIC_WORKSPACE -u SERVICEFABRIC_HOME -u PYTHONPATH PATH="$(dir $(WAVE06_PYTHON)):$(PATH)" $(WAVE06_PYTHON) -m pip check
	$(WAVE06_ENV) $(WAVE06_PYTHON) -m compileall packages/servicefabric_capability_mcp_projection packages/servicefabric_capability_consumers services/capability_rest_gateway services/mcp_gateway clients/python tests/capability_mcp_projection tests/capability_rest_gateway tests/capability_consumers tests/wave_06
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
