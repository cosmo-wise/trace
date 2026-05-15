/**
 * Trace Schemas — Evidence protocol contract definitions.
 *
 * These types define the stable evidence protocol consumed by
 * harness, trial, compass, and stirrup for artifact verification,
 * audit, and cross-module evidence indexing.
 *
 * @module trace/schemas
 * @version 1
 */

// ─── Run Manifest ──────────────────────────────────────────────────

/** The trace run manifest (run.json). */
export interface TraceRunManifest {
  run_id: string;
  status: "running" | "completed" | "failed" | "cancelled";
  label?: string;
  started_at?: string;  // ISO 8601
  completed_at?: string; // ISO 8601
  sensitivity_level: "public" | "internal" | "restricted" | "confidential";
  provenance?: {
    tool: string;
    version: string;
    host?: string;
  };
}

// ─── Timeline Events ───────────────────────────────────────────────

/** A single timeline event (timeline.jsonl line). */
export interface TraceEvent {
  event_id: string;
  run_id: string;
  timestamp: string;     // ISO 8601
  type: string;          // e.g. "artifact_added", "phase_started"
  module: string;        // e.g. "harness", "trial", "compass"
  phase: string;         // e.g. "generation", "evaluation"
  status: "ok" | "warning" | "error";
  message: string;
  detail?: Record<string, unknown>;
}

// ─── Artifacts ──────────────────────────────────────────────────────

/** Standard artifact type identifier. */
export type ArtifactType =
  | "code" | "config" | "screenshot" | "log"
  | "trace-event" | "report" | "test-result" | "coverage"
  | "diff" | "manifest" | "artifact-bundle"
  | "evidence" | "metadata";

/** Standard artifact role. */
export type ArtifactRole =
  | "source" | "output" | "evidence" | "reference"
  | "intermediate" | "final";

/** An artifact entry in the index. */
export interface ArtifactEntry {
  id: string;
  type: ArtifactType;
  path: string;
  size_bytes: number;
  role?: ArtifactRole;
  content_hash?: string;
  metadata?: Record<string, unknown>;
}

/** The artifact index (artifacts/index.json). */
export interface ArtifactIndex {
  artifacts: ArtifactEntry[];
  /** The standard type registry version used. */
  type_registry_version?: number;
}

// ─── Module Health ──────────────────────────────────────────────────

/** Module health status for a single module. */
export interface ModuleHealth {
  status: "ok" | "degraded" | "error";
  message?: string;
  events_total: number;
  events_by_status: Record<string, number>;
}

// ─── Summary ────────────────────────────────────────────────────────

/**
 * The trace summary (summary-1.0.json).
 * This is the primary consumer-facing artifact for downstream modules.
 */
export interface TraceSummary {
  version: number; // 1
  run_id: string;
  status: string;
  label?: string;
  started_at?: string;
  completed_at?: string;
  modules: Record<string, string>;  // module_name -> status
  artifacts: {
    total: number;
    by_type: Record<string, number>;
    total_bytes: number;
  };
  events: {
    total: number;
    by_status: Record<string, number>;
  };
  module_health: Record<string, ModuleHealth>;
  sensitivity_level: string;
  provenance?: Record<string, unknown>;
}

// ─── Compass / Portal ───────────────────────────────────────────────

/** Compass portal digest (compass-digest.json) — consumed by compass ingester. */
export interface TraceCompassDigest {
  run_id: string;
  status: string;
  artifactCount: number;
  moduleHealth?: Record<string, ModuleHealth>;
}

// ─── Audit Export ───────────────────────────────────────────────────

/** Audit export for compliance and review. */
export interface TraceAuditExport {
  run_id: string;
  generated_at: string;
  summary: TraceSummary;
  events: TraceEvent[];
  artifacts: ArtifactEntry[];
}
