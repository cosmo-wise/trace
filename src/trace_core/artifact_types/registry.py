"""ArtifactTypeRegistry for managing and validating artifact roles and types."""

from __future__ import annotations

from trace_core.artifact_types.standard_roles import STANDARD_ROLES
from trace_core.artifact_types.standard_types import STANDARD_TYPES


class ArtifactTypeRegistry:
    """Registry for standard artifact roles and types with validation."""

    def __init__(
        self,
        extra_roles: dict[str, str] | None = None,
        extra_types: dict[str, str] | None = None,
    ) -> None:
        self._roles = dict(STANDARD_ROLES)
        self._types = dict(STANDARD_TYPES)
        if extra_roles:
            self._roles.update(extra_roles)
        if extra_types:
            self._types.update(extra_types)

    def validate_role(self, role: str) -> bool:
        """Check if a role is registered."""
        return role in self._roles

    def validate_type(self, artifact_type: str) -> bool:
        """Check if an artifact type is registered."""
        return artifact_type in self._types

    def lookup_role(self, role: str) -> str | None:
        """Get the description for a role, or None if not found."""
        return self._roles.get(role)

    def lookup_type(self, artifact_type: str) -> str | None:
        """Get the description for a type, or None if not found."""
        return self._types.get(artifact_type)

    def list_roles(self) -> dict[str, str]:
        """List all registered roles with descriptions."""
        return dict(self._roles)

    def list_types(self) -> dict[str, str]:
        """List all registered types with descriptions."""
        return dict(self._types)

    def register_role(self, role: str, description: str) -> None:
        """Register an additional role."""
        self._roles[role] = description

    def register_type(self, artifact_type: str, description: str) -> None:
        """Register an additional artifact type."""
        self._types[artifact_type] = description
