"""Tests for trace artifact type registry."""

from __future__ import annotations

from trace_core.artifact_types import ArtifactTypeRegistry


def test_registry_standard_roles() -> None:
    registry = ArtifactTypeRegistry()
    assert registry.validate_role("source") is True
    assert registry.validate_role("nonexistent") is False


def test_registry_standard_types() -> None:
    registry = ArtifactTypeRegistry()
    assert registry.validate_type("code") is True
    assert registry.validate_type("screenshot") is True
    assert registry.validate_type("invalid_type") is False


def test_registry_custom_role() -> None:
    registry = ArtifactTypeRegistry(extra_roles={"custom": "Custom role"})
    assert registry.validate_role("custom") is True
    assert registry.lookup_role("custom") == "Custom role"


def test_registry_list_roles() -> None:
    registry = ArtifactTypeRegistry()
    roles = registry.list_roles()
    assert isinstance(roles, dict)
    assert len(roles) > 0
