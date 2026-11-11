---
name: dev-dude-feature-implementation
description: >
  Internal DevDude functional skill for implementation clarification, planning, production
  changes, and mandatory paired test implementation from an approved design.
version: 1.1.4
---

# DevDude Feature Implementation

Start with a fresh context. This skill runs only as a stage dispatched by the DevDude controller;
it is a loader and holds no policy text.

1. Require a root-validated YAML input handoff whose `policy_context` (HOC-SCHEMA-001.R16) gives an
   absolute `policy_manifest` inside a supported installed root (`policies/platform.yaml`
   `root_discovery`) with matching digest, plus the run `policy_snapshot` and pinned
   `model_profile_snapshot` with their digests. Absent,
   ambiguous, or mismatched -> return `blocked` (POLICY ROOT GATE). Never search project and user
   scopes to guess, and never run directly without a handoff.
2. Load manifest load set `stage.dev-dude-feature-implementation` from that root. The workflow is the root copy
   `skills/dev-dude-feature-implementation/references/workflow.yaml`; this installed skill's `version` must equal
   `policies/metadata.yaml` `crews.skills.version`, otherwise return `blocked` (STAGE VERSION GATE).
   Before applying it, re-hash every loaded file with a runtime hashing tool and compare it with
   the `policy_snapshot` (manifest.yaml `integrity`); a changed or unhashable file returns
   `blocked` (POLICY INTEGRITY GATE).
3. Execute the workflow policies in file order, with FSK-CONTRACT-001, FSK-MON-001, ENV-001 and
   STG-* governing contracts, monitoring, envelopes and the stage lifecycle. Children take models
   from the snapshot and receive the same `policy_context` (policy and model snapshots included).

This stage has no Markdown examples. Loading is instruction-driven; no runtime enforces it.
