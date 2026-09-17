---
name: dev-dude-architecture
description: >
  Internal DevDude functional skill for architecture discovery, investigation, documentation,
  operator vertical review, verification, architecture critique, and correction.
version: 1.0.0
---

# DevDude Architecture

Execute the architecture run described in [references/workflow.md](references/workflow.md).

Accept only a root-orchestrator handoff containing a reconciled run-state path, current step,
orchestration envelope, `$INDEXER_CONTEXT`, command scope, and expected exit evidence. Stay inside
this architecture workflow. Checkpoint each delegated task and gate, then return evidence and
control to the root DevDude orchestrator.
