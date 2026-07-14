"""ServiceFabric Process Runtime management library."""

from __future__ import annotations

from servicefabric_process_runtime.controller import ManagedProcessController
from servicefabric_process_runtime.errors import (
    PortAllocationError,
    ProcessRuntimeError,
    ProcessStartError,
    StaleProcessError,
)
from servicefabric_process_runtime.identity import (
    get_process_fields,
    is_alive,
    is_owned_process,
    is_same_process,
)
from servicefabric_process_runtime.models import (
    HealthTarget,
    ProcessIdentity,
    ProcessResourceSnapshot,
    ProcessStatus,
    ResolvedProcessPlan,
)
from servicefabric_process_runtime.ports import allocate_loopback_port
from servicefabric_process_runtime.records import ModuleRuntimeRecord, ModuleRuntimeStore
from servicefabric_process_runtime.resolution import ProcessPlanResolver
from servicefabric_framework_kits import ASGIProcessPlan

__all__ = [
    "ManagedProcessController",
    "PortAllocationError",
    "ProcessRuntimeError",
    "ProcessStartError",
    "StaleProcessError",
    "get_process_fields",
    "is_alive",
    "is_owned_process",
    "is_same_process",
    "HealthTarget",
    "ProcessIdentity",
    "ProcessResourceSnapshot",
    "ProcessStatus",
    "ResolvedProcessPlan",
    "allocate_loopback_port",
    "ModuleRuntimeRecord",
    "ModuleRuntimeStore",
    "ProcessPlanResolver",
    "ASGIProcessPlan",
]
