# Quant-Fabric Architect
## Objective
Generate micro-apps for the `6_service_catalog/` directory that perform quantitative financial analysis (backtesting, risk modeling, real-time ticker tracking) while adhering to Service Fabric's hub-and-spoke event model and Vite-based frontend pipeline.

## Implementation Rules
- **Data Handling**: Always prefer **Polars** or **NumPy** for backend calculations in `service.py` to ensure performance within the FaaS execution window.
- **Real-Time Flow**: Use the `FabricSDK` to broadcast price updates or signal alerts. Never instantiate standalone WebSockets; always route through the FastAPI Gateway.
- **Frontend**: Utilize **Svelte 5** (via the `vite_base` template) for reactive financial dashboards. Use `@fabric/shared` components for consistent UI.
- **Storage**: Multi-dimensional time-series data should be scoped to the `owner_id` using the platform's PostgreSQL instance.

## Standard Quant App Structure
- `service.py`: The Engine. Place backtesting logic or Alpha-factor generation here.
- `routes.py`: The API. Define endpoints for results and rebalancing.
- `tasks.py`: Data Ingestion. Periodic jobs for fetching prices from external APIs.
- `src/App.svelte`: The Terminal. Use Svelte's runes ($state) for real-time data handling.
