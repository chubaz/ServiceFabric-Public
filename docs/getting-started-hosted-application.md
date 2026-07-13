# Run the first hosted application locally

Create a Python 3.11 environment and install the repository packages in editable mode. Install the Text Utility's pinned runtime dependencies (`fastapi==0.139.0` and `uvicorn==0.51.0`) and the first-class `servicefabric-application-host` and `servicefabric-client` packages.

Then use only the installed command:

```bash
export SERVICEFABRIC_HOME=/tmp/servicefabric-local
servicefabric init
servicefabric apps install examples/text-utility
servicefabric apps build text-utility
servicefabric apps start text-utility
servicefabric apps status text-utility
servicefabric apps resources text-utility
servicefabric tools list
servicefabric tools describe text.count_words
servicefabric call text.count_words \
  --input '{"text":"ServiceFabric hosts applications and capabilities."}'
servicefabric apps stop text-utility
```

The host binds only to `127.0.0.1`. The capability call passes through a canonical request and reviewed policy before the application adapter is invoked. Once stopped, the capability is unavailable.

This alpha slice supports one reviewed FastAPI package and local process metrics. It does not provide public hosting, production identity, TLS, distributed scheduling, dynamic package commands, or automatic capability publication.
