from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "servicefabric_application_model",
    "servicefabric_application_assembly",
    "servicefabric_process_runtime",
    "servicefabric_workspace",
    "servicefabric_framework_kits",
):
    sys.path.insert(0, str(ROOT / "packages" / package))
sys.path.insert(0, str(ROOT / "services" / "application_dev_supervisor"))

from servicefabric_application_assembly import ApplicationAssembly, ApplicationResource, ModuleAssemblyNode
from servicefabric_application_dev_supervisor import ApplicationDevelopmentSupervisor, SupervisorError
from servicefabric_process_runtime import ProcessResourceSnapshot, ProcessStatus


class FakeProcesses:
    def __init__(self, fail_on: str | None = None):
        self.fail_on, self.calls, self.states = fail_on, [], {}

    def start(self, plan):
        self.calls.append(("start", plan.module_id))
        if plan.module_id == self.fail_on:
            raise RuntimeError("not ready")
        status = ProcessStatus("running", None, 9000 + len(self.states), "healthy", 1.0)
        self.states[plan.module_id] = status
        return status

    def stop(self, application_id, module_id):
        self.calls.append(("stop", module_id))
        status = ProcessStatus("stopped", None, None, "unavailable", None)
        self.states[module_id] = status
        return status

    def status(self, application_id, module_id):
        return self.states.get(module_id, ProcessStatus("stopped", None, None, "unavailable", None))

    def logs(self, application_id, module_id, maximum_bytes):
        self.calls.append(("logs", module_id, maximum_bytes))
        return "tail"

    def resources(self, application_id, module_id):
        return ProcessResourceSnapshot(12, 20, 1.5)


class FakeResources:
    def __init__(self): self.calls = []
    def prepare(self, application_id, resources):
        self.calls.append(("prepare", tuple(resources)))
        return {resource_id: f"binding:{resource_id}" for resource_id in resources}
    def release(self, application_id, resource_ids): self.calls.append(("release", resource_ids))
    def status(self, application_id, resource_id): return "ready"


class Plan:
    def __init__(self, module_id): self.module_id = module_id


def assembly():
    nodes = {module_id: ModuleAssemblyNode(module_id, None, (), (), (), (), ()) for module_id in ("database-client", "api", "web")}
    return ApplicationAssembly(nodes, {}, {"database.primary": ApplicationResource("database.primary", "sqlite", "application", ("api",))}, (), ("database-client", "api", "web"), ("database-client", "api", "web"), ("web", "api", "database-client"))


def supervisor(processes=None, resources=None, prepared=None):
    processes, resources, prepared = processes or FakeProcesses(), resources or FakeResources(), prepared if prepared is not None else []
    service = ApplicationDevelopmentSupervisor(assembly(), processes, resources, lambda node, bindings: prepared.append(node.module_id), lambda node, bindings: None if node.module_id == "database-client" else Plan(node.module_id))
    return service, processes, resources, prepared


class SupervisorTests(unittest.TestCase):
    def test_prepare_and_start_follow_deterministic_orders(self):
        service, processes, resources, prepared = supervisor()
        status = service.start("notes")
        self.assertEqual(prepared, ["database-client", "api", "web"])
        self.assertEqual(processes.calls, [("start", "api"), ("start", "web")])
        self.assertEqual(resources.calls[0], ("prepare", ("database.primary",)))
        self.assertEqual(status.state, "running")
        self.assertFalse(status.modules["database-client"].executable)

    def test_failed_start_rolls_back_started_modules_and_resources(self):
        service, processes, resources, _ = supervisor(FakeProcesses(fail_on="web"))
        with self.assertRaises(SupervisorError): service.start("notes")
        self.assertEqual(processes.calls, [("start", "api"), ("start", "web"), ("stop", "api")])
        self.assertEqual(resources.calls[-1], ("release", ("database.primary",)))

    def test_restart_only_stops_and_starts_requested_module(self):
        service, processes, _, _ = supervisor()
        service.start("notes")
        service.restart("notes", "api")
        self.assertEqual(processes.calls[-2:], [("stop", "api"), ("start", "api")])
        self.assertEqual(processes.status("notes", "web").state, "running")

    def test_stop_is_reverse_order_and_releases_resources(self):
        service, processes, resources, _ = supervisor()
        service.start("notes")
        status = service.stop("notes")
        self.assertEqual(processes.calls[-2:], [("stop", "web"), ("stop", "api")])
        self.assertEqual(resources.calls[-1], ("release", ("database.primary",)))
        self.assertEqual(status.state, "stopped")

    def test_status_logs_and_observations_are_bounded_and_targeted(self):
        service, processes, _, _ = supervisor()
        service.start("notes")
        self.assertEqual(service.logs("notes", "api", 32), "tail")
        self.assertEqual(processes.calls[-1], ("logs", "api", 32))
        self.assertEqual(service.observe("notes", "api").resources.peak_memory_bytes, 20)
        with self.assertRaises(ValueError): service.logs("notes", "api", 0)
        with self.assertRaises(SupervisorError): service.restart("notes", "missing")
