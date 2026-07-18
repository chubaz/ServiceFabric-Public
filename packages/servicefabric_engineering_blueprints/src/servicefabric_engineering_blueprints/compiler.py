"""Deterministic, provider-neutral engineering-blueprint compilation."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath

from servicefabric_agentic_contracts import AgentRunPlan, AgentTask, ApplicationIntent
from servicefabric_agentic_planner import PlanValidationError, compile_plan
from servicefabric_application_factory_contracts import (
    EngineeringBlueprint,
    EngineeringLane,
    TechnologyProfile,
)
from servicefabric_blueprints import ApplicationBlueprint


class BlueprintCompilationError(ValueError):
    """Raised when reviewed inputs cannot form a safe engineering plan."""


_INTEGRATION_LANE_ID = "application-integration"
_ACCEPTANCE_LANE_ID = "application-assurance"
_REQUIRED_CONTEXT = ("AGENTS.md",)


def _path(path: str, *, lane_id: str) -> str:
    candidate = PurePosixPath(path)
    if (
        not path
        or candidate.is_absolute()
        or "\\" in path
        or ".." in candidate.parts
        or candidate == PurePosixPath(".")
    ):
        raise BlueprintCompilationError(
            f"lane {lane_id!r} has unsafe allowed path {path!r}"
        )
    return candidate.as_posix()


def _paths_overlap(left: str, right: str) -> bool:
    left_parts = PurePosixPath(left).parts
    right_parts = PurePosixPath(right).parts
    shared_length = min(len(left_parts), len(right_parts))
    return left_parts[:shared_length] == right_parts[:shared_length]


def _validate_reviewed_inputs(
    blueprint: ApplicationBlueprint, profile: TechnologyProfile
) -> tuple[object, ...]:
    if not profile.approved:
        raise BlueprintCompilationError("technology profile must be approved")
    if profile.unresolved_requirements:
        raise BlueprintCompilationError(
            "technology profile has unresolved requirements: "
            + ", ".join(profile.unresolved_requirements)
        )
    if (
        profile.application_blueprint_id != blueprint.blueprint_id
        or profile.application_blueprint_version != blueprint.version
    ):
        raise BlueprintCompilationError(
            "technology profile does not match the exact application blueprint version"
        )

    modules = blueprint.load_modules()
    selections = {selection.module_id: selection for selection in profile.module_selections}
    module_ids = {module.module_id for module in modules}
    if set(selections) != module_ids:
        raise BlueprintCompilationError(
            "technology profile selections must match blueprint modules exactly"
        )
    for module in modules:
        primitive = getattr(module.primitive, "value", module.primitive)
        if selections[module.module_id].primitive != str(primitive):
            raise BlueprintCompilationError(
                f"technology profile primitive does not match module {module.module_id!r}"
            )
    return modules


def _module_dependencies(modules: tuple[object, ...]) -> dict[str, tuple[str, ...]]:
    interface_owner = {
        interface.id: module.module_id
        for module in modules
        for interface in module.provides_interfaces
    }
    dependencies: dict[str, tuple[str, ...]] = {}
    for module in modules:
        required = (
            interface_owner[interface.id]
            for interface in module.requires_interfaces
            if interface.id in interface_owner
            and interface_owner[interface.id] != module.module_id
        )
        dependencies[module.module_id] = tuple(sorted(set(required)))
    return dependencies


def _default_lanes(
    modules: tuple[object, ...], profile: TechnologyProfile
) -> tuple[EngineeringLane, ...]:
    selections = {selection.module_id: selection for selection in profile.module_selections}
    dependencies = _module_dependencies(modules)
    module_lanes = tuple(
        EngineeringLane(
            lane_id=f"module-{module.module_id}",
            role="implementation",
            module_ids=(module.module_id,),
            dependencies=tuple(f"module-{item}" for item in dependencies[module.module_id]),
            allowed_paths=(_path(module.source, lane_id=module.module_id),),
            required_context=_REQUIRED_CONTEXT,
            expected_outputs=(module.source,),
            verification_commands=("python3 -m unittest",),
            provider_role=selections[module.module_id].provider_role,
        )
        for module in sorted(modules, key=lambda item: item.module_id)
    )
    module_lane_ids = tuple(lane.lane_id for lane in module_lanes)
    return module_lanes + (
        EngineeringLane(
            lane_id=_INTEGRATION_LANE_ID,
            role="integration",
            dependencies=module_lane_ids,
            allowed_paths=(".servicefabric/application-integration",),
            required_context=_REQUIRED_CONTEXT,
            expected_outputs=("application integration record",),
            verification_commands=("python3 -m unittest",),
            provider_role="integration",
            integration_owned=True,
        ),
        EngineeringLane(
            lane_id=_ACCEPTANCE_LANE_ID,
            role="assurance",
            dependencies=(_INTEGRATION_LANE_ID,),
            allowed_paths=(".servicefabric/application-assurance",),
            required_context=_REQUIRED_CONTEXT,
            expected_outputs=("application verification evidence",),
            verification_commands=("python3 -m unittest",),
            provider_role="assurance",
        ),
    )


def _validate_lanes(lanes: tuple[EngineeringLane, ...]) -> None:
    ids = tuple(lane.lane_id for lane in lanes)
    if len(set(ids)) != len(ids):
        raise BlueprintCompilationError("engineering lane IDs must be unique")
    known_ids = set(ids)
    owned_paths: list[tuple[str, str]] = []
    integration_lanes = [lane for lane in lanes if lane.integration_owned]
    if len(integration_lanes) != 1:
        raise BlueprintCompilationError("exactly one lane must own application integration")

    for lane in lanes:
        if not lane.allowed_paths:
            raise BlueprintCompilationError(f"lane {lane.lane_id!r} must declare allowed paths")
        unknown = set(lane.dependencies) - known_ids
        if unknown:
            raise BlueprintCompilationError(
                f"lane {lane.lane_id!r} has unknown dependencies: {', '.join(sorted(unknown))}"
            )
        if lane.lane_id in lane.dependencies:
            raise BlueprintCompilationError(f"lane {lane.lane_id!r} cannot depend on itself")
        lane_paths: set[str] = set()
        for path in lane.allowed_paths:
            normalized = _path(path, lane_id=lane.lane_id)
            if normalized in lane_paths:
                raise BlueprintCompilationError(
                    f"lane {lane.lane_id!r} duplicates normalized allowed path {normalized!r}"
                )
            lane_paths.add(normalized)
            for owned_path, owner in owned_paths:
                if _paths_overlap(owned_path, normalized):
                    raise BlueprintCompilationError(
                        f"lanes {owner!r} and {lane.lane_id!r} have overlapping "
                        f"allowed paths {owned_path!r} and {normalized!r}"
                    )
            owned_paths.append((normalized, lane.lane_id))


def _tasks_from_lanes(lanes: tuple[EngineeringLane, ...]) -> tuple[AgentTask, ...]:
    return tuple(
        AgentTask(
            task_id=lane.lane_id,
            role=lane.role,
            objective=f"{lane.role} lane for {', '.join(lane.module_ids) or 'application'}",
            dependencies=lane.dependencies,
            allowed_paths=lane.allowed_paths,
            forbidden_paths=lane.forbidden_paths,
            required_context=lane.required_context,
            expected_outputs=lane.expected_outputs,
            verification_commands=lane.verification_commands,
        )
        for lane in lanes
    )


def compile_engineering_blueprint(
    intent: ApplicationIntent,
    application_blueprint: ApplicationBlueprint,
    technology_profile: TechnologyProfile,
    *,
    blueprint_id: str | None = None,
    run_id: str | None = None,
    maximum_parallel_tasks: int = 2,
    lanes: Iterable[EngineeringLane] | None = None,
) -> EngineeringBlueprint:
    """Compiles approved inputs into isolated candidate lanes and an ``AgentRunPlan``.

    The function plans only: it neither creates repositories nor executes a
    provider.  Callers may supply reviewed lanes; otherwise one lane per module,
    followed by integration and assurance lanes, is derived deterministically.
    """
    if not 1 <= maximum_parallel_tasks <= 64:
        raise BlueprintCompilationError("maximum_parallel_tasks must be between 1 and 64")
    modules = _validate_reviewed_inputs(application_blueprint, technology_profile)
    compiled_lanes = _default_lanes(modules, technology_profile) if lanes is None else tuple(lanes)
    _validate_lanes(compiled_lanes)

    integration_lane = next(lane for lane in compiled_lanes if lane.integration_owned)
    acceptance_lanes = [lane for lane in compiled_lanes if lane.role == "assurance"]
    if len(acceptance_lanes) != 1:
        raise BlueprintCompilationError("exactly one assurance lane is required")
    try:
        plan: AgentRunPlan = compile_plan(
            intent,
            run_id=run_id or f"engineering-{intent.intent_id}",
            maximum_parallel_tasks=maximum_parallel_tasks,
            tasks=_tasks_from_lanes(compiled_lanes),
        )
    except PlanValidationError as error:
        raise BlueprintCompilationError(str(error)) from error
    return EngineeringBlueprint(
        blueprint_id=blueprint_id or f"engineering-{application_blueprint.blueprint_id}",
        application_id=intent.application_id or application_blueprint.blueprint_id,
        application_blueprint_id=application_blueprint.blueprint_id,
        technology_profile_id=technology_profile.profile_id,
        agent_run_plan=plan,
        lanes=compiled_lanes,
        integration_lane_id=integration_lane.lane_id,
        acceptance_lane_id=acceptance_lanes[0].lane_id,
        maximum_parallel_tasks=maximum_parallel_tasks,
    )
