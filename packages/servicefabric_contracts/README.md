# ServiceFabric Contracts

This package contains framework-neutral, declarative contracts. It does not host,
discover, invoke, or expose tools. `ServicePackageDefinition` describes a package;
`ToolDefinition` describes one stable bounded operation; `ToolRevision` captures
its immutable executable contract; `ToolDeployment` and `ToolStatus` keep desired
deployment state separate from observed operational state.

See `docs/contracts/service-package-v1alpha1.md` for the v1alpha1 contract guide.
The public package is `0.2.0a1`; all resources remain explicitly alpha under
`servicefabric.ai/v1alpha1`.
