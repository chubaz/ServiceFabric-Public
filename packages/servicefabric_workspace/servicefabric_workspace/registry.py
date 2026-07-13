"""Registry for local applications within the workspace."""

from __future__ import annotations

import json
from pathlib import Path

from servicefabric_workspace.errors import ApplicationAlreadyExists, ApplicationNotFound
from servicefabric_workspace.filesystem import atomic_write_text
from servicefabric_workspace.models import ApplicationRecord


class ApplicationRegistry:
    """Manages file-backed local application registration records."""

    def __init__(self, registry_dir: Path):
        self.registry_dir = registry_dir
        self.applications_dir = registry_dir / "applications"

    def register(
        self,
        application_id: str,
        display_name: str,
        source_path: str,
        status: str = "development",
    ) -> ApplicationRecord:
        """Registers a new application record in the registry folder atomically.

        Args:
            application_id: The unique application identifier.
            display_name: The descriptive display name.
            source_path: Relative path from workspace root to the application folder.
            status: Active development status.

        Returns:
            The created ApplicationRecord.

        Raises:
            ApplicationAlreadyExists: If the application is already registered.
        """
        self.applications_dir.mkdir(parents=True, exist_ok=True)
        record_path = self.applications_dir / f"{application_id}.json"
        
        if record_path.is_file():
            raise ApplicationAlreadyExists(f"application '{application_id}' is already registered")

        record_data = {
            "format": 1,
            "application_id": application_id,
            "display_name": display_name,
            "source_path": source_path,
            "status": status,
        }

        atomic_write_text(record_path, json.dumps(record_data, indent=2) + "\n")
        
        return ApplicationRecord(
            application_id=application_id,
            display_name=display_name,
            source_path=source_path,
            status=status,
        )

    def get(self, application_id: str) -> ApplicationRecord:
        """Retrieves a registered application record.

        Raises:
            ApplicationNotFound: If the record does not exist on disk.
        """
        record_path = self.applications_dir / f"{application_id}.json"
        if not record_path.is_file():
            raise ApplicationNotFound(f"application '{application_id}' is not registered")

        try:
            with record_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                return ApplicationRecord(
                    application_id=data["application_id"],
                    display_name=data["display_name"],
                    source_path=data["source_path"],
                    status=data["status"],
                )
        except Exception as exc:
            raise ApplicationNotFound(
                f"Failed to load registry record for application '{application_id}': {exc}"
            ) from exc

    def list(self) -> tuple[ApplicationRecord, ...]:
        """Enumerates all registered application records deterministically (alphabetically by ID)."""
        if not self.applications_dir.is_dir():
            return ()

        records: list[ApplicationRecord] = []
        for path in sorted(self.applications_dir.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                    records.append(
                        ApplicationRecord(
                            application_id=data["application_id"],
                            display_name=data["display_name"],
                            source_path=data["source_path"],
                            status=data["status"],
                        )
                    )
            except Exception:
                # Silently ignore malformed registry files in this fast listing
                pass

        return tuple(records)
