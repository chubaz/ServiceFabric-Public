# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Service Fabric** is a modular microservices platform that hosts multiple mini-apps ("services") from a shared infrastructure. It follows a numbered-directory organization:

```
1_proxy/              # Nginx reverse proxy
2_backend_api/        # Django 5 REST API (auth, user mgmt, service registry)
3_service_templates/  # Blueprint templates for creating new services
4_generated_services/ # Auto-generated service instances
5_core_services/      # Core engines: Flask (orchestrator) + Vite builders
6_service_catalog/    # The deployed service apps (Svelte/React frontends + Python backends)
7_user_media/         # User file uploads, isolated by user_id
```

## Development Commands

### Start the full stack (development)
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```
- Dev mode mounts live source code for hot reload
- Django runs `runserver` instead of Gunicorn
- Django API directly accessible at `http://localhost:8002`
- App accessible via Nginx at `http://localhost:8080`
- Env vars from `.env.dev`

### Start production stack
```bash
docker-compose up -d
```
- Uses `.env.prod`
- Gunicorn (4 workers), Vite in PERIODIC build mode (every 5 min)

### Django management (inside container)
```bash
docker-compose exec backend_api python manage.py migrate
docker-compose exec backend_api python manage.py createsuperuser
docker-compose exec backend_api python manage.py collectstatic
```

### Rebuild a specific service image
```bash
docker-compose build backend_api
docker-compose build core_flask_service
```

## Architecture: How the Pieces Connect

### Request Flow
```
Browser → Nginx (1_proxy) → Django API (2_backend_api) [/api/*]
                           → Flask Core (5_core_services/flask_base) [/core/*]
                           → Static assets built by Vite [/static/*, /dist/*]
```

### Frontend Build Pipeline
`5_core_services/vite_base/builder.js` is the build orchestrator:
- Discovers every directory in `6_service_catalog/` that has a `src/main.ts`
- Uses a single shared `vite.config.ts` with `TARGET_APP_ROOT` and `TARGET_OUT_DIR` env vars
- Symlinks `node_modules` from the builder into `6_service_catalog/node_modules` so all services share deps
- Three build modes: `WATCH` (live), `ONCE` (single pass), `PERIODIC` (timed, default in prod)
- Output lands in `flask_static` Docker volume, served by Flask/Nginx

For **React** services: handled by `5_core_services/vite_react_core/` (separate builder, same pattern)

### Dynamic Service Execution (FaaS)
Flask route `POST /core/execute/<instance_id>` loads and runs `service.py` from a service catalog directory on-the-fly (like AWS Lambda). Every service instance is scoped to `owner_id` — never query without this filter.

### Authentication & Templates
- Django issues JWT tokens (15-min access, 7-day refresh)
- Flask middleware (`app/middleware.py`) validates JWT on `@token_required` routes via `g.user_id`
- **Template Discovery**: Flask uses a `ChoiceLoader` to merge local, shared, and blueprint templates. If you modify the loader in `create_app`, you must chain the `original_loader` to maintain shard functionality.
- All Flask API endpoints except `/core/status` require auth

## Service Catalog Pattern

Each service in `6_service_catalog/` follows this structure:
```
service_name/
├── src/              # Frontend source (Svelte: main.ts / React: main.jsx)
├── models.py         # SQLAlchemy models
├── routes.py         # Flask blueprint with API endpoints
├── service.py        # Business logic / FaaS entry point
├── schemas.py        # Validation schemas
└── tasks.py          # Background tasks
```

Services with `src/main.ts` are Svelte 5 apps; services with `src/main.jsx` are React 18 apps.

The `6_service_catalog/_shared/` directory contains shared Svelte components, aliased as `@fabric/shared` in `vite.config.ts`.

## Key Technology Versions

| Layer | Tech | Version |
|---|---|---|
| Frontend (primary) | Svelte | 5.0 |
| Frontend (alt) | React | 18.2 |
| Build tool | Vite | 6.0 (Svelte), 5.1 (React) |
| CSS | Tailwind | 4.0 (Svelte), 3.3 (React) |
| Backend API | Django + DRF | 5.0 |
| Orchestrator | Flask | 3.0 |
| Database | PostgreSQL | 15 |
| Proxy | Nginx | latest |
| Runtime | Python | 3.11, Node 20 |

## Environment Files

- `.env.dev` — development secrets (Django `SECRET_KEY`, DB credentials, API keys)
- `.env.prod` — production secrets
- `.env.example` — template showing required variables

## Adding a New Service

1. Create a directory in `6_service_catalog/<service_name>/`
2. Add `src/main.ts` (Svelte) or `src/main.jsx` (React) — the builder auto-discovers it
3. Add `routes.py` with a Flask blueprint registered in Flask's app factory
4. Add `models.py` for any DB tables needed
5. The Vite builder will automatically pick it up on next build cycle
