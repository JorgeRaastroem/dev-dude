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
- Treat `complete`, `cancelled`, and `abandoned` as terminal statuses. The latter two require an
  explicit durable user decision and must not authorize continuation.
- Confirm the declared receiving stage and next objective are permitted by the workflow version.

## Evidence Pass

- Require at least one specific, resolvable evidence locator for every verified fact and every
  completion criterion marked `met`.
- Confirm referenced artifacts exist, are accessible, and are declared.
- When an artifact has a digest, recompute and compare it before accepting the contract.
- Permit `.tmp/` locators only in nonterminal contracts whose receiving stage still consumes them and
  whose run state requires preservation. A terminal contract must resolve all final evidence through
  durable artifacts.
- Downgrade unsupported claims to assumptions/open questions or fail validation; never preserve a
  false `verified` label.

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
- A `cancelled` or `abandoned` contract may retain unmet criteria only when it records the explicit
  user decision, retained durable outputs, superseded pending work, and no receiving stage or
  continuation authorization.
- `partial`, `blocked`, and `failed` contracts cannot advance to a different stage.
- Confirm required downstream inputs are present and artifact/tool authorization is least-context.
- The workflow definition prevails over a conflicting handoff unless a referenced, authorized,
  versioned amendment exists.
- Confirm any user approval has durable evidence; never infer it from status or conversation.
- After authorized cleanup, do not revalidate an immutable historical contract as a current
  transition. Reconcile through the latest terminal contract and cleanup checkpoint; the historical
  `.tmp/` locator and recorded deletion remain audit evidence, not authorization to advance.

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

For independent replay, the receiving stage must be able to initialize and explain its permitted
knowledge using only the workflow, contract, authorized artifacts, and current-stage tool results.
