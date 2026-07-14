"""ProcessPlanResolver translating unresolved kit plans into ResolvedProcessPlan."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from servicefabric_application_model import ModuleDefinition
from servicefabric_framework_kits import (
    ASGIProcessPlan,
    HealthPlan,
    KitPlanningContext,
    ProcessPlan,
)
from servicefabric_workspace import ApplicationLayout, WorkspaceLayout
from servicefabric_workspace.filesystem import check_managed_path_symlink, ensure_descendant
from servicefabric_process_runtime.errors import ProcessRuntimeError
from servicefabric_process_runtime.models import HealthTarget, ResolvedProcessPlan
from servicefabric_process_runtime.ports import allocate_loopback_port


class ProcessPlanResolver:
    """Resolves unresolved framework-kit plans into fully executable ResolvedProcessPlan."""

    def resolve(
        self,
        *,
        application: ApplicationLayout,
        module: ModuleDefinition,
        process_plan: ProcessPlan,
        health_plan: HealthPlan,
        workspace: WorkspaceLayout,
    ) -> ResolvedProcessPlan:
        """Resolves portable plans into machine-specific, validated execution plans.

        Raises:
            ProcessRuntimeError: If security boundaries or validation rules are violated.
        """
        # 1. Enforce strict adapter check
        if process_plan.adapter_id != "python-asgi":
            raise ProcessRuntimeError(
                f"Unsupported adapter ID '{process_plan.adapter_id}'. Only 'python-asgi' is supported."
            )

        # 2. Path safety validations (symlinks and descendants)
        try:
            resolved_src = (application.root / module.source).resolve()
        except Exception as exc:
            raise ProcessRuntimeError(f"Failed to resolve module source path: {exc}") from exc

        check_managed_path_symlink(resolved_src)
        check_managed_path_symlink(application.root)
        ensure_descendant(application.root, resolved_src)

        # 3. Validate ASGI import string format (e.g., 'package:app')
        if ":" not in process_plan.application_import:
            raise ProcessRuntimeError(
                f"Invalid ASGI import string '{process_plan.application_import}': "
                "must be formatted as 'package:app'."
            )

        # 4. Enforce strict loopback binding policy
        if process_plan.host != "127.0.0.1":
            raise ProcessRuntimeError(
                f"Security violation: non-loopback bind host '{process_plan.host}' is prohibited."
            )

        # 5. Resolve python executable from environment or fallback to system python
        env_python = workspace.environments / application.application_id / "bin" / "python3"
        if not env_python.is_file():
            executable = Path(sys.executable)
        else:
            executable = env_python

        # 6. Allocate loopback port dynamically
        port = None
        if process_plan.port_binding == "allocated":
            port = allocate_loopback_port()

        # 7. Translate launcher specification into exact uvicorn arguments list
        arguments = ["-m", "uvicorn", process_plan.application_import]
        arguments.extend(["--host", process_plan.host])
        if port is not None:
            arguments.extend(["--port", str(port)])
        
        # Turn off access log for text-utility legacy compliance or if specified
        if not process_plan.access_log or module.module_id == "text-utility":
            arguments.append("--no-access-log")
        if process_plan.reload:
            arguments.append("--reload")

        # 8. Setup log path under workspace state
        log_dir = workspace.logs / "applications" / application.application_id
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{module.module_id}.log"

        # 9. Build environment variables
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(resolved_src)
        if port is not None:
            environment["SF_MODULE_PORT"] = str(port)

        # 10. Resolve health probe target
        probe_path = "/health"
        if health_plan.path:
            probe_path = health_plan.path
        
        health_url = f"http://127.0.0.1:{port}{probe_path}" if port is not None else None
        health_target = HealthTarget(
            probe_type=health_plan.probe_type,
            url=health_url,
            timeout_seconds=health_plan.timeout_seconds,
        )

        # Retrieve shutdown timeout from lifecycle configuration
        shutdown_timeout = float(module.lifecycle.shutdown.timeout_seconds)

        return ResolvedProcessPlan(
            application_id=application.application_id,
            module_id=module.module_id,
            adapter_id=process_plan.adapter_id,
            executable=executable,
            arguments=tuple(arguments),
            working_directory=resolved_src,
            environment=environment,
            log_path=log_path,
            port=port,
            health_target=health_target,
            shutdown_timeout_seconds=shutdown_timeout,
        )
