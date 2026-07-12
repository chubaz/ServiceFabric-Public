# Python Dependency Build Baseline

P0-06 makes Python service images build from service-local direct dependency inputs and committed runtime locks.

## Supported Target

- Python runtime target: CPython 3.11 on Debian slim images.
- Production services: `backend_api`, `core_flask_service`, `fastapi_core`.
- Development-only retained service: `fabric_watcher`.

## Lock Structure

Each Python service owns:

- `requirements/runtime.in`: human-maintained direct runtime dependencies.
- `requirements/runtime.lock`: generated exact transitive pins committed to Git.

Compatibility `requirements.txt` files point to the runtime lock and are no longer the source of production dependency truth.

Regenerate locks with:

```bash
python3 -m venv /tmp/servicefabric-p0-06-lock-venv
/tmp/servicefabric-p0-06-lock-venv/bin/python -m pip install --upgrade pip pip-tools
PIP_TOOLS_CACHE_DIR=/tmp/servicefabric-pip-tools-cache \
PIP_CACHE_DIR=/tmp/servicefabric-pip-cache \
pip-compile --resolver=backtracking --no-emit-index-url --no-emit-trusted-host \
  --allow-unsafe \
  --output-file 2_backend_api/requirements/runtime.lock \
  2_backend_api/requirements/runtime.in
```

Repeat for each service-local `requirements/runtime.in`.

Validate committed locks with:

```bash
python3 scripts/dependencies/check_python_locks.py
python3 scripts/dependencies/check_python_locks.py --verify-compile
```

The second command requires `pip-tools` and network access to package indexes unless metadata is already cached.

## Flask Dependency Containment

The production Flask host now contains only the legacy hosting dependencies currently imported by the app or immutable catalogue snapshot. The following packages were removed from the universal Flask production runtime because current production code does not import them and the packaged catalogue contains no approved service requiring them:

- Agent frameworks: `crewai`, `langchain_openai`, `langchain_community`.
- Vector and embedding clients: `chromadb`, `google-genai`.
- Document and scraping packages: `PyPDF2`, `markdown`, `googlesearch-python`, `beautifulsoup4`.
- Data-science packages: `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `polars`.
- Quantitative finance packages: `yfinance`, `quantstats`.
- Miscellaneous unsupported runtime packages: `psutil`, `requests`, `Flask-WTF`.

These packages are candidates for future domain capsule images or explicitly approved immutable legacy catalogue artifacts. They must not be reintroduced into the universal Flask production image without an approved runtime owner and lock file.

## CI Expectations

CI should run the structural dependency checker on every change. Where Docker builds are available, CI should also build the Python production images and run `python -m pip check` inside each built image.
