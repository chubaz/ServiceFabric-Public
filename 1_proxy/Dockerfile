FROM node:20.11-alpine AS svelte-assets
WORKDIR /app/builder

# Frontend builds are a release-time operation. The currently approved catalogue
# snapshot may contain no active applications; this stage still produces a stable artifact directory.
COPY 5_core_services/vite_base/package*.json ./
COPY 5_core_services/vite_base/builder.js 5_core_services/vite_base/vite.config.ts ./
COPY 6_service_catalog /app/services_catalog
RUN npm ci --legacy-peer-deps && mkdir -p /app/dist/svelte && BUILD_MODE=ONCE node builder.js

FROM node:20.11-alpine AS react-assets
WORKDIR /app/builder
COPY 5_core_services/react_base/package*.json ./
COPY 5_core_services/react_base/builder.js 5_core_services/react_base/vite.config.ts ./
COPY 6_service_catalog /app/services_catalog
RUN npm ci && mkdir -p /app/dist/react && BUILD_MODE=ONCE node builder.js

FROM nginxinc/nginx-unprivileged:1.25-alpine
COPY 1_proxy/conf.d/default.conf /etc/nginx/conf.d/default.conf
COPY --from=svelte-assets /app/dist/svelte/ /usr/share/nginx/html/catalog/svelte/
COPY --from=react-assets /app/dist/react/ /usr/share/nginx/html/catalog/react/
USER nginx
