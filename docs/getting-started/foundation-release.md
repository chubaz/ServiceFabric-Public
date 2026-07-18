# Foundation release: five-minute demonstration

The foundation release presents the current canonical ServiceFabric packages as a local engineering platform. It does not require containers, a database, credentials, or a remote inventory for this demonstration.

## 1. Install the release-readiness command

From the repository root, use Python 3.11 or newer:

```bash
python3 -m pip install -e packages/servicefabric_release_readiness
```

## 2. Check the local foundation

```bash
servicefabric doctor --repository-root .
```

The command checks the Python version and that each package declared in the foundation-release manifest exists with the expected project metadata. It makes no changes: it does not install dependencies, provision resources, read secrets, or contact remote services.

For automation, request JSON:

```bash
servicefabric doctor --repository-root . --json
```

## 3. Explore the canonical capabilities

Read [the foundation capability reference](../reference/foundation-capabilities.md) for the supported architecture surface and [the product overview](../architecture/product-overview.md) for how the parts compose.

The doctor verifies release layout, not application behavior. Use the relevant package tests and workplans when developing a capability.
