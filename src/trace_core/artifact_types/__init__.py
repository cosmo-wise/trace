"""Standard artifact role and type registry for trace evidence."""

from trace_core.artifact_types.registry import ArtifactTypeRegistry
from trace_core.artifact_types.standard_roles import STANDARD_ROLES
from trace_core.artifact_types.standard_types import STANDARD_TYPES

__all__ = ["ArtifactTypeRegistry", "STANDARD_ROLES", "STANDARD_TYPES"]
