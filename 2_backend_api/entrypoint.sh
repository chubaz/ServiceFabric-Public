#!/bin/sh
set -eu

if [ "${FABRIC_ENVIRONMENT:-development}" = "production" ]; then
  for name in SECRET_KEY DJANGO_SECRET_KEY DATABASE_URL ALLOWED_HOSTS JWT_SECRET_KEY JWT_ISSUER JWT_AUDIENCE; do
    value=$(printenv "$name" || true)
    case "$value" in
      ''|*change_me*|replace_*|*yourdomain.com*)
        echo "Production configuration is invalid: $name must be explicitly configured" >&2
        exit 1
        ;;
    esac
  done
fi

# Schema migration, static collection, and bootstrap are explicit release operations.
exec gunicorn myproject.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
  --access-logfile - \
  --error-logfile -
