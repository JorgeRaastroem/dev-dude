# Handoff Validation Rules

The root orchestrator validates every input and output contract before transition. Validation is
independent of the producing stage's assertions and has four passes.

## Structural Pass

- Parse the contract as YAML and require every schema section.
- Require schema version `1.0`, valid status/enumeration values, stable workflow/run identity, unique
  identifiers, and a unique contract identifier.
- Resolve every `based_on`, evidence, required-input, continuation, and authorization reference to a
  declared item.
- Require receiving-stage fields for nonterminal work and prohibit them for terminal work.
- Confirm the declared receiving stage and next objective are permitted by the workflow version.

## Evidence Pass

- Require at least one specific, resolvable evidence locator for every verified fact and every
  completion criterion marked `met`.
- Confirm referenced artifacts exist, are accessible, and are declared.
- When an artifact has a digest, recompute and compare it before accepting the contract.
- Downgrade unsupported claims to assumptions/open questions or fail validation; never preserve a
  false `verified` label.
- An elapsed deadline, cancellation request, missing artifact, or stale journal is not termination
  evidence. Reject unsupported stopped/cancelled claims with `UNVERIFIED_TERMINATION`.

## Epistemic Pass

- Keep facts, assumptions, constraints, decisions, rejected approaches, questions, blockers,
  failures, and artifacts separate.
- Require decisions and rejections to reference their supporting facts or constraints.
- Detect conflicting claims. They must be explicitly represented as blocking questions until
  resolved.
- Reject confidence language used in place of evidence and assumption-to-fact promotion without new
  evidence.
- Reject raw transcripts, chain-of-thought, scratchpads, tool chatter, or irrelevant context.

## Workflow Pass

- Confirm the producing stage stayed in its declared scope and evaluated all completion criteria.
- A `complete` contract cannot contain unmet applicable criteria, blockers, blocking questions, or
  unresolved failures.
- `partial`, `blocked`, and `failed` contracts cannot advance to a different stage.
- Confirm required downstream inputs are present and artifact/tool authorization is least-context.
- The workflow definition prevails over a conflicting handoff unless a referenced, authorized,
  versioned amendment exists.
- Confirm any user approval has durable evidence; never infer it from status or conversation.
- Before recovery dispatch or stage advancement, establish completion or verified termination of
  prior invocations and descendants and reconcile partial outputs and side effects. Active or
  unknown execution blocks retry, replacement work, and overlapping writes (`EXECUTION_NOT_QUIESCENT`).
  Pause recovery on unknown status; missing cancellation alone does not block initial dispatch.

## Outcome

Record one of:

```yaml
validation:
  result: "pass"
  validated_by: "root-contract-gate"
  issues: []
```

```yaml
validation:
  result: "fail"
  validated_by: "root-contract-gate"
  issues:
    - code: "MISSING_EVIDENCE"
      location: "verified_facts[F003]"
      message: "The claim has no resolvable evidence reference."
      remediation: "Add specific evidence or reclassify the claim as an assumption."
```

Every failure issue requires a stable code, exact field location, message, and actionable
remediation. Do not dispatch work on failure. Return the issues to the producing stage, or stop at a
gate when remediation requires user action.

## Adversarial Checks

Use this matrix to evaluate changes to stage workflows and when a suspicious handoff is received:

| Scenario | Required result |
|---|---|
| Verified claim has no evidence | Fail with `MISSING_EVIDENCE` or reclassify before resubmission |
| A later stage promotes an assumption | Preserve the type; verify independently or block |
| Required information exists only in chat | Treat it as unavailable |
| A digested artifact changed | Fail with `DIGEST_MISMATCH` and revalidate |
| Artifacts support contradictory claims | Record both and block or route to resolution |
| Stage performs later-stage work | Fail with `SCOPE_VIOLATION` |
| A criterion is unmet but status is complete | Fail with `INCOMPLETE_STAGE` |
| Contract contains transcript or raw reasoning | Fail with `EXCESS_CONTEXT` |
| Handoff conflicts with workflow | Fail with `WORKFLOW_CONFLICT`; workflow wins |
| Fresh agent receives only allowed inputs | It can restate objective, allowed knowledge, and limits |
| Neither cancellation nor enforced timeout is available; input is valid and no prior work is active | Dispatch cooperatively through the supported mechanism, record limitations and bounded objective/checkpoint instructions; no capability-only approval gate |
| Verified cancellation or enforced timeout is available | Retain controlled watchdog checks, deadline handling, termination verification, and three-retry limit |
| Cooperative action is active after its deadline | Record `deadline exceeded`, keep execution status active, monitor without claiming cancellation or retrying |
| Synchronous cooperative invocation prevents live checks | Record monitoring limitation before launch; reconcile on return/resume; promise neither interruption nor bounded return time |
| Deadline elapsed or cancellation was requested, but stopped/cancelled is claimed without evidence | Fail with `UNVERIFIED_TERMINATION`; keep deadline and execution status separate |
| Status is unknown on resume and outputs are missing or journal is stale | Checkpoint `execution status unknown` and `recovery-paused`; do not reset to pending or launch duplicate/replacement work |
| Parent returned but a descendant is active or unknown | Block retry, stage advancement, and overlapping writes/cleanup with `EXECUTION_NOT_QUIESCENT` |
| User approves a retry while prior work may remain active | Approval cannot substitute for termination evidence; recovery stays paused |
| Completion and descendant quiescence are confirmed after a deadline; output satisfies criteria | Reconcile outputs, validate normally, and continue without replaying completed work |
| Prior invocation and descendants are verified stopped; output is partial | Reconcile partial outputs and side effects, retry only safe incomplete work under the same action ID and persisted budget |
| Three retries are exhausted, or a repeat has uncertain side effects/conflicting work/scope change | Preserve exhaustion as bounded-unresolved, or use the existing safety/approval gate; never reset budgets or infer approval |

For independent replay, the receiving stage must be able to initialize and explain its permitted
knowledge using only the workflow, contract, authorized artifacts, and current-stage tool results.
