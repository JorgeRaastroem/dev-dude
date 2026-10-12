---
name: dev-dude-validation
description: >
  Internal DevDude functional skill for project checks, semantic verification, final validator
  decisions, and bounded remediation routing.
version: 1.1.3
---

# DevDude Validation

Execute [references/workflow.md](references/workflow.md).

Apply the supplied orchestration-state policy's controlled/cooperative monitoring to every child
invocation. Record capabilities and limitations in the stage journal, checkpoint progress, and
return partial or blocked results when appropriate. Missing cancellation alone does not block
dispatch; an elapsed deadline does not prove termination. No retry, replacement, or overlapping
writes until prior work and descendants are confirmed quiescent and partial outputs reconciled.

Accept only a root-validated YAML handoff containing reconciled state, authorized feature spec and
approved design, implementation/test evidence, changed paths, orchestration envelope,
`$INDEXER_CONTEXT`, and current/max validation attempts. Treat the invocation as a fresh, bounded
stage: use only this workflow, the contract, authorized artifacts and tools, and evidence retrieved
now. Restate the objective and completion criteria. Run the completion gate and return a typed
contract with `SATISFIED`, a targeted remediation route, or bounded-unresolved evidence. Do not
implement remediation. Never recover missing state from prior conversation or include raw reasoning
in the handoff.
