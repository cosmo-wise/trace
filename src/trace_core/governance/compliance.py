"""
Trace Governance — enterprise evidence integrity, custody, and compliance.

Extends the base trace protocol with:
- Chain-of-custody tracking for audit evidence
- Evidence integrity verification (hash-based)
- Enterprise compliance redaction presets (GDPR, HIPAA, PCI)
- Sensitivity classification enforcement
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


# ─── Sensitivity Classification ────────────────────────────────────

class SensitivityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"


class ComplianceStandard(str, Enum):
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI = "pci"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


# ─── Enterprise Redaction Presets ───────────────────────────────────

ENTERPRISE_REDACTION_PRESETS: dict[str, dict[str, Any]] = {
    "gdpr": {
        "label": "GDPR Personal Data",
        "patterns": [
            r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Full names
            r"\b[\w.-]+@[\w.-]+\.\w{2,}\b",   # Email addresses
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",  # IP addresses
        ],
        "field_names": [
            "email", "name", "phone", "address", "ip_address",
            "personal_data", "user_name", "customer_name",
        ],
    },
    "hipaa": {
        "label": "HIPAA Protected Health Information",
        "patterns": [
            r"\b\d{3}-\d{2}-\d{4}\b",          # SSN-like
            r"\b(patient|diagnosis|treatment)\b",
            r"\bMRN[:\s]*\d+\b",
        ],
        "field_names": [
            "patient_id", "mrn", "diagnosis", "treatment",
            "health_record", "medical_data", "phi",
        ],
    },
    "pci": {
        "label": "PCI Cardholder Data",
        "patterns": [
            r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",  # Card numbers
            r"\b\d{3,4}\b",                                # CVV/CVC
        ],
        "field_names": [
            "card_number", "cvv", "cvc", "pan",
            "credit_card", "payment_info",
        ],
    },
}


# ─── Chain of Custody ────────────────────────────────────────────────

@dataclass
class CustodyEntry:
    action: str                      # "created", "transferred", "verified", "exported"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    actor: str = "system"
    detail: str | None = None
    hash_after: str | None = None    # integrity hash after action

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "detail": self.detail,
            "hash_after": self.hash_after,
        }


class ChainOfCustody:
    """Track the chain of custody for evidence artifacts."""

    def __init__(self, evidence_id: str) -> None:
        self.evidence_id = evidence_id
        self.entries: list[CustodyEntry] = []
        self._add_entry("created")

    def _add_entry(self, action: str, detail: str | None = None, hash_after: str | None = None) -> None:
        self.entries.append(CustodyEntry(
            action=action,
            detail=detail,
            hash_after=hash_after,
        ))

    def record_transfer(self, destination: str, hash_after: str | None = None) -> None:
        self._add_entry("transferred", f"to {destination}", hash_after)

    def record_verification(self, result: str, hash_after: str | None = None) -> None:
        self._add_entry("verified", result, hash_after)

    def record_export(self, export_path: str, hash_after: str | None = None) -> None:
        self._add_entry("exported", f"to {export_path}", hash_after)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "chain": [e.to_dict() for e in self.entries],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


# ─── Integrity Verification ──────────────────────────────────────────

def compute_file_hash(path: Path, algorithm: str = "sha256") -> str:
    """Compute a hash for a file for integrity verification."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"{algorithm}:{h.hexdigest()}"


def compute_directory_hash(dir_path: Path, algorithm: str = "sha256") -> str:
    """Compute a combined hash for a directory (sorts files for determinism)."""
    h = hashlib.new(algorithm)
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            h.update(file_path.relative_to(dir_path).as_posix().encode())
            h.update(compute_file_hash(file_path, algorithm).encode())
    return f"{algorithm}:{h.hexdigest()}"


def verify_integrity(
    dir_path: Path,
    expected_hash: str,
    algorithm: str = "sha256",
) -> dict[str, Any]:
    """Verify directory integrity against an expected hash."""
    actual = compute_directory_hash(dir_path, algorithm)
    match = actual == expected_hash
    return {
        "verified": match,
        "expected": expected_hash,
        "actual": actual,
        "algorithm": algorithm,
    }


# ─── Evidence Bundle Manifest ────────────────────────────────────────

@dataclass
class EvidenceBundleManifest:
    """Manifest for an evidence bundle with integrity and custody data."""

    bundle_id: str
    run_id: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    compliance_standards: list[str] = field(default_factory=list)
    sensitivity: SensitivityLevel = SensitivityLevel.INTERNAL
    redaction_applied: bool = False
    redaction_presets: list[str] = field(default_factory=list)
    integrity_hash: str | None = None
    custody: dict[str, Any] = field(default_factory=dict)
    artifacts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "compliance": {
                "standards": self.compliance_standards,
                "sensitivity": self.sensitivity.value,
                "redaction_applied": self.redaction_applied,
                "redaction_presets": self.redaction_presets,
            },
            "integrity": {
                "hash": self.integrity_hash,
            },
            "custody": self.custody,
            "artifacts_count": len(self.artifacts),
        }

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


# ─── Compliance Validator ────────────────────────────────────────────

def validate_compliance(
    bundle_manifest: EvidenceBundleManifest,
    required_standards: list[str],
) -> dict[str, Any]:
    """Validate that a bundle meets required compliance standards."""
    missing = set(required_standards) - set(bundle_manifest.compliance_standards)
    return {
        "compliant": len(missing) == 0,
        "required": required_standards,
        "satisfied": list(set(required_standards) & set(bundle_manifest.compliance_standards)),
        "missing": list(missing),
        "sensitivity_adequate": (
            bundle_manifest.sensitivity
            in {SensitivityLevel.RESTRICTED, SensitivityLevel.CONFIDENTIAL}
        ),
    }
