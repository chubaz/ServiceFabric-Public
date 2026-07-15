"""Lifecycle orchestration for a deterministic application assembly.

This boundary deliberately accepts prepared launch plans and resource bindings from
other lanes.  It owns ordering, rollback, aggregate observations, and the
in-memory records needed to explain a supervisor operation; it does not create
providers, framework-kit plans, or subprocesses itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Protocol

from servicefabric_application_assembly import ApplicationAssembly, ApplicationResource, ModuleAssemblyNode
from servicefabric_process_runtime import ProcessResourceSnapshot, ProcessStatus, ResolvedProcessPlan


class SupervisorError(RuntimeError):
    """Raised when a bounded supervisor operation cannot complete."""


class ProcessController(Protocol):
    def start(self, plan: ResolvedProcessPlan) -> ProcessStatus: ...
    def stop(self, application_id: str, module_id: str) -> ProcessStatus: ...
    def status(self, application_id: str, module_id: str) -> ProcessStatus: ...
    def logs(self, application_id: str, module_id: str, maximum_bytes: int) -> str: ...
    def resources(self, application_id: str, module_id: str) -> ProcessResourceSnapshot: ...


class ResourceLifecycle(Protocol):
    def prepare(self, application_id: str, resources: Mapping[str, ApplicationResource]) -> Mapping[str, str]: ...
    def release(self, application_id: str, resource_ids: tuple[str, ...]) -> None: ...
    def status(self, application_id: str, resource_id: str) -> str: ...


PlanFactory = Callable[[ModuleAssemblyNode, Mapping[str, str]], ResolvedProcessPlan | None]
ModulePreparer = Callable[[ModuleAssemblyNode, Mapping[str, str]], None]


@dataclass(frozen=True)
class ModuleRecord:
    """Supervisor-owned summary of one orchestration decision."""

    module_id: str
    state: str
    health: str
    port: int | None
    executable: bool


@dataclass(frozen=True)
class ModuleObservation:
    module_id: str
    status: ProcessStatus
    resources: ProcessResourceSnapshot


@dataclass(frozen=True)
class AggregateStatus:
    application_id: str
    state: str
    modules: Mapping[str, ModuleRecord]
    resources: Mapping[str, str]


class ApplicationDevelopmentSupervisor:
    """Coordinates resource, preparation, and process lifecycle boundaries."""

    def __init__(
        self,
        assembly: ApplicationAssembly,
        processes: ProcessController,
        resources: ResourceLifecycle,
        prepare_module: ModulePreparer,
        create_plan: PlanFactory,
    ) -> None:
        self._assembly = assembly
        self._processes = processes
        self._resources = resources
        self._prepare_module = prepare_module
        self._create_plan = create_plan
        self._bindings: Mapping[str, str] = {}
        self._prepared = False
        self._records: dict[str, ModuleRecord] = {}

    def prepare(self, application_id: str) -> AggregateStatus:
        """Prepare resources and modules deterministically, without starting processes."""
        self._bindings = dict(self._resources.prepare(application_id, self._assembly.resources_by_id))
        try:
            for module_id in self._assembly.build_order:
                self._prepare_module(self._assembly.modules_by_id[module_id], self._bindings)
            self._prepared = True
        except Exception as exc:
            self._resources.release(application_id, tuple(self._assembly.resources_by_id))
            self._bindings = {}
            self._prepared = False
            raise SupervisorError("Application preparation failed; prepared resources were released.") from exc
        return self.status(application_id)

    def start(self, application_id: str) -> AggregateStatus:
        """Start executable modules in assembly order and roll back on first failure."""
        if not self._prepared:
            self.prepare(application_id)
        started: list[str] = []
        failing_module: str | None = None
        try:
            for module_id in self._assembly.startup_order:
                failing_module = module_id
                node = self._assembly.modules_by_id[module_id]
                plan = self._create_plan(node, self._bindings)
                if plan is None:
                    self._records[module_id] = ModuleRecord(module_id, "ready", "not-applicable", None, False)
                    continue
                status = self._processes.start(plan)
                started.append(module_id)
                self._records[module_id] = _record(module_id, status, True)
        except Exception as exc:
            for module_id in reversed(started):
                self._records[module_id] = _record(module_id, self._processes.stop(application_id, module_id), True)
            self._resources.release(application_id, tuple(self._assembly.resources_by_id))
            self._bindings = {}
            self._prepared = False
            detail = ""
            if failing_module is not None:
                try:
                    trailing_log = self._processes.logs(application_id, failing_module, 4096)
                except Exception:
                    trailing_log = ""
                if trailing_log:
                    for value in self._bindings.values():
                        if value:
                            trailing_log = trailing_log.replace(value, "[redacted]")
                    detail = f" Trailing process log:\n{trailing_log}"
                raise SupervisorError(
                    f"Application startup failed for module '{failing_module}'; started modules were rolled back.{detail}"
                ) from exc
            raise SupervisorError("Application startup failed; started modules were rolled back.") from exc
        return self.status(application_id)

    def restart(self, application_id: str, module_id: str) -> ModuleRecord:
        """Restart exactly one executable module; no dependency is rebuilt or restarted."""
        node = self._node(module_id)
        if not self._prepared:
            self.prepare(application_id)
        plan = self._create_plan(node, self._bindings)
        if plan is None:
            raise SupervisorError(f"Module '{module_id}' has no executable process plan.")
        self._processes.stop(application_id, module_id)
        record = _record(module_id, self._processes.start(plan), True)
        self._records[module_id] = record
        return record

    def stop(self, application_id: str) -> AggregateStatus:
        """Stop executable modules in shutdown order, then release application resources."""
        failures: list[str] = []
        for module_id in self._assembly.shutdown_order:
            node = self._assembly.modules_by_id[module_id]
            if self._create_plan(node, self._bindings) is None:
                continue
            try:
                self._records[module_id] = _record(module_id, self._processes.stop(application_id, module_id), True)
            except Exception:
                failures.append(module_id)
        if failures:
            raise SupervisorError(f"Application shutdown could not stop module(s): {', '.join(failures)}")
        self._resources.release(application_id, tuple(self._assembly.resources_by_id))
        self._bindings = {}
        self._prepared = False
        return self.status(application_id)

    def status(self, application_id: str) -> AggregateStatus:
        """Return an aggregate view without changing module lifecycle state."""
        records: dict[str, ModuleRecord] = {}
        for module_id, node in self._assembly.modules_by_id.items():
            executable = self._create_plan(node, self._bindings) is not None
            if executable:
                records[module_id] = _record(module_id, self._processes.status(application_id, module_id), True)
            else:
                records[module_id] = self._records.get(module_id, ModuleRecord(module_id, "ready", "not-applicable", None, False))
        resource_states = {resource_id: self._resources.status(application_id, resource_id) for resource_id in self._assembly.resources_by_id}
        states = {record.state for record in records.values()}
        state = "failed" if "failed" in states else "running" if states and states <= {"running", "ready"} else "stopped"
        return AggregateStatus(application_id, state, records, resource_states)

    def logs(self, application_id: str, module_id: str, maximum_bytes: int) -> str:
        """Return a bounded trailing log view for an executable module."""
        if maximum_bytes < 1:
            raise ValueError("maximum_bytes must be positive")
        self._node(module_id)
        return self._processes.logs(application_id, module_id, maximum_bytes)

    def observe(self, application_id: str, module_id: str) -> ModuleObservation:
        """Return current process and resource observations for one executable module."""
        self._node(module_id)
        return ModuleObservation(module_id, self._processes.status(application_id, module_id), self._processes.resources(application_id, module_id))

    def _node(self, module_id: str) -> ModuleAssemblyNode:
        try:
            return self._assembly.modules_by_id[module_id]
        except KeyError as exc:
            raise SupervisorError(f"Unknown module '{module_id}'.") from exc


def _record(module_id: str, status: ProcessStatus, executable: bool) -> ModuleRecord:
    return ModuleRecord(module_id, status.state, status.health, status.port, executable)
