---
name: dev-dude-feature-implementation
description: >
  Internal DevDude functional skill for implementation clarification, planning, production
  changes, and mandatory paired test implementation from an approved design.
version: 1.1.0
---

# DevDude Feature Implementation

Execute [references/workflow.md](references/workflow.md).

Accept only a root-validated YAML handoff containing reconciled state, explicit design approval,
authorized durable feature documents and `$INDEXER_CONTEXT`, orchestration envelope, and expected
exit evidence. Treat the invocation as a fresh, bounded stage: use only this workflow, the contract,
authorized artifacts and tools, and evidence retrieved now. Restate the objective and completion
criteria. Do not own final validation. Return a typed contract containing implementation and
paired-test evidence to root for dispatch to `dev-dude-validation`. Never recover missing state from
prior conversation or include raw reasoning in the handoff.
