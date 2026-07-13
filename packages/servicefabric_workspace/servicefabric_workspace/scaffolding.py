"""Utilities for scaffolding empty ServiceFabric applications."""

from __future__ import annotations

from servicefabric_workspace.models import ApplicationLayout


def scaffold_application(layout: ApplicationLayout, display_name: str) -> None:
    """Generates the empty application directory layout and default scaffolding files.

    All directory structures are created and populated with minimal placeholders.
    """
    # 1. Create standard modules and tests directories
    layout.root.mkdir(parents=True, exist_ok=True)
    layout.modules.mkdir(parents=True, exist_ok=True)
    layout.tests.mkdir(parents=True, exist_ok=True)
    layout.documentation.mkdir(parents=True, exist_ok=True)
    layout.metadata.mkdir(parents=True, exist_ok=True)
    layout.generated.mkdir(parents=True, exist_ok=True)

    # 2. Write Markdown documentation files
    readme_content = (
        f"# {display_name}\n\n"
        f"This is the `{layout.application_id}` ServiceFabric application.\n\n"
        "Refer to `DEVELOPMENT.md` for details on building, testing, and running the application, "
        "and `ARCHITECTURE.md` for its design.\n"
    )
    layout.readme_file.write_text(readme_content, encoding="utf-8")

    agents_content = (
        "# Application Development Instructions\n\n"
        f"This directory contains the `{layout.application_id}` ServiceFabric application.\n\n"
        "## Editable areas\n\n"
        "- `modules/`\n"
        "- `tests/`\n"
        "- `README.md`\n"
        "- `ARCHITECTURE.md`\n"
        "- `DEVELOPMENT.md`\n"
        "- application configuration under `.servicefabric/`, except `generated/`\n\n"
        "## Protected areas\n\n"
        "- Do not modify files outside this application directory.\n"
        "- Do not modify `.servicefabric/generated/` manually.\n"
        "- Do not write credentials into source files.\n"
        "- Do not hard-code ServiceFabric workspace paths.\n"
    )
    layout.agents_file.write_text(agents_content, encoding="utf-8")

    arch_content = (
        f"# Architecture of {display_name}\n\n"
        f"This is the architectural overview of the `{layout.application_id}` application.\n"
    )
    layout.architecture_file.write_text(arch_content, encoding="utf-8")

    dev_content = (
        f"# Development Guide for {display_name}\n\n"
        f"This guide outlines how to build, test, and run the `{layout.application_id}` application.\n"
    )
    layout.development_file.write_text(dev_content, encoding="utf-8")

    # 3. Write minimal YAML definitions as stable extension points
    app_yaml_content = (
        "apiVersion: servicefabric.local/v1\n"
        "kind: Application\n\n"
        "metadata:\n"
        f"  id: {layout.application_id}\n"
        f"  name: {display_name}\n\n"
        "spec:\n"
        "  status: development\n"
        "  modules: []\n"
    )
    layout.application_definition.write_text(app_yaml_content, encoding="utf-8")

    blueprint_yaml_content = (
        "apiVersion: servicefabric.local/v1\n"
        "kind: ApplicationBlueprint\n\n"
        "metadata:\n"
        f"  applicationId: {layout.application_id}\n\n"
        "spec:\n"
        "  source: empty\n"
        "  modules: []\n"
        "  frameworkKits: []\n"
        "  requestedResources: []\n"
    )
    layout.blueprint.write_text(blueprint_yaml_content, encoding="utf-8")

    bindings_yaml_content = (
        "apiVersion: servicefabric.local/v1\n"
        "kind: ApplicationBindings\n\n"
        "metadata:\n"
        f"  applicationId: {layout.application_id}\n\n"
        "spec:\n"
        "  bindings: {}\n"
    )
    layout.bindings.write_text(bindings_yaml_content, encoding="utf-8")

    dev_config_content = (
        "apiVersion: servicefabric.local/v1\n"
        "kind: DevelopmentConfiguration\n\n"
        "metadata:\n"
        f"  applicationId: {layout.application_id}\n\n"
        "spec:\n"
        "  commands: {}\n"
        "  requiredChecks: []\n"
    )
    layout.development_config.write_text(dev_config_content, encoding="utf-8")
