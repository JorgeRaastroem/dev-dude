---
name: dev-dude-feature-design
description: >
  Internal DevDude functional skill for feature investigation, trusted resource research, design
  options, architecture critique, refinement, and explicit user design selection.
version: 1.0.0
---

# DevDude Feature Design

Execute [references/workflow.md](references/workflow.md).

Accept only a root-orchestrator handoff containing reconciled state, the feature input and slug,
orchestration envelope, `$INDEXER_CONTEXT`, `$RESOURCE_RESEARCH_CONTEXT`, trusted-source policy
path, and expected exit evidence. Stop after explicit design approval. Do not clarify
implementation, plan work, change production code, or validate a feature. Return evidence and
control to the root DevDude orchestrator.
