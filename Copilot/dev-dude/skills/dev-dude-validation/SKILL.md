---
name: dev-dude-validation
description: >
  Internal DevDude functional skill for project checks, semantic verification, final validator
  decisions, and bounded remediation routing.
version: 1.0.0
---

# DevDude Validation

Execute [references/workflow.md](references/workflow.md).

Accept only a root-orchestrator handoff containing reconciled state, the feature spec and approved
design, implementation/test evidence, changed paths, orchestration envelope, `$INDEXER_CONTEXT`,
and current/max validation attempts. Run the completion gate and return `SATISFIED`, a targeted
remediation route, or bounded-unresolved evidence. Do not implement remediation; return control to
the root DevDude orchestrator.
