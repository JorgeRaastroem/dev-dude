---
name: dev-dude-feature-design
description: >
  Internal DevDude functional skill for feature investigation, trusted resource research, design
  options, architecture critique, refinement, and explicit user design selection.
version: 1.1.0
---

# DevDude Feature Design

Execute [references/workflow.md](references/workflow.md).

Accept only a root-validated YAML handoff containing reconciled state, the feature input and slug,
orchestration envelope, authorized `$INDEXER_CONTEXT` and `$RESOURCE_RESEARCH_CONTEXT`,
trusted-source policy path, and expected exit evidence. Treat the invocation as a fresh, bounded
stage: use only this workflow, the contract, authorized artifacts and tools, and evidence retrieved
now. Restate the objective and completion criteria. Stop after explicit design approval; do not
clarify implementation, plan work, change production code, or validate a feature. Return a typed
output contract and control to root. Never recover missing state from prior conversation or include
raw reasoning in the handoff.
