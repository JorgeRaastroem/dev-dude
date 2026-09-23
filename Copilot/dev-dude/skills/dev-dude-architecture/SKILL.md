---
name: dev-dude-architecture
description: >
  Internal DevDude functional skill for architecture discovery, investigation, documentation,
  operator vertical review, verification, architecture critique, and correction.
version: 1.1.0
---

# DevDude Architecture

Execute the architecture run described in [references/workflow.md](references/workflow.md).

Accept only a root-validated YAML handoff containing a reconciled run-state path, current step,
orchestration envelope, `$INDEXER_CONTEXT`, command scope, and expected exit evidence. Treat the
invocation as a fresh, bounded stage: use only this workflow, the contract, authorized artifacts and
tools, and evidence retrieved now. Restate the objective and completion criteria, stay inside this
workflow, checkpoint each task and gate, then return a typed output contract and control to root.
Never recover missing state from prior conversation or include raw reasoning in the handoff.
