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

The package manifest is allowlisted and binds the application source files to reviewed SHA-256 digests. Build publication and process startup reverify those files and the immutable artifact. Application state is replaced atomically and mutating commands are serialized with a local file lock. A stale process ID is not trusted unless its Linux process start time and fixed reviewed command also match.

`apps resources` separates package declarations from observations. On Linux it samples the managed process-group leader's RSS and CPU time over a 50 ms interval; it does not aggregate child-process memory or CPU. Missing or unsupported observations are reported as `null`, never zero. Startup duration, health, request count, and restart count come from the managed host record. The child log file is capped at 1 MiB; exceeding that local host policy can terminate the application rather than consume unbounded disk.

This alpha slice supports one reviewed FastAPI package, Linux local process hosting, and local process metrics. It does not provide public hosting, production identity, TLS, distributed scheduling, dynamic package commands, child-process resource aggregation, portable non-Linux process observation, or automatic capability publication. AP-00 remains responsible for general framework adapters; AP-01B remains responsible for broader resource-aware hosting.
