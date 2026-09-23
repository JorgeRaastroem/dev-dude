# Epistemic Stage Workflow

Every functional-skill invocation is a named, bounded stage. The root orchestrator owns stage
transitions and applies this lifecycle at every boundary.

## Epistemic Firewall

Stage N may use only:

1. the applicable, versioned workflow definition;
2. its validated input handoff contract;
3. artifacts and tools authorized by that contract; and
4. applicable shared policies and contract definitions supplied by the root; and
5. tool results retrieved and verified during Stage N.

Prior conversation, hidden reasoning, scratchpads, tool chatter, and unreferenced artifacts are
untrusted history. If a needed item is absent, classify it as an open question, retrieve it when
authorized, or stop with a blocker. Never reconstruct it from conversational memory.

## Stage Declaration

Before dispatch, the root records a stable stage name and the stage's:

- bounded objective;
- required contract fields and authorized artifacts/tools;
- expected durable outputs;
- completion criteria; and
- permitted next stage or terminal state.

The workflow definition and an explicit, versioned workflow amendment are the only authorities that
may change objective, scope, constraints, or transitions. A handoff cannot amend its workflow.

## Lifecycle

1. **Initialize fresh context.** Supply only the stage declaration, validated contract, authorized
   artifacts, applicable shared policies, and tool capabilities.
2. **Validate input.** Apply [validation-rules.md](validation-rules.md). Resolve referenced artifacts
   and evidence. Do not execute the stage when validation fails.
3. **Restate the objective.** Record the bounded objective and measurable completion criteria before
   work begins.
4. **Execute in scope.** Keep verified facts, assumptions, constraints, decisions, rejected
   approaches, open questions, blockers, and artifacts distinct.
5. **Verify results.** Evaluate every completion criterion and re-check material claims. Independently
   reverify inherited facts before high-impact or irreversible actions.
6. **Serialize output.** Write the next YAML contract using
   [handoff-contract-schema.md](handoff-contract-schema.md). Include conclusions and evidence, never
   chain-of-thought or raw exploration.
7. **Validate output.** The root runs the contract gate. A new stage starts only after `pass`.
8. **Discard working context.** The validated contract and its authorized artifacts are the stage's
   only durable output.

## Transition Storage

Store contracts beside the run state:

```text
<run-output>/
├── .dev-dude-run-state.md
└── .dev-dude-handoffs/
    ├── 000-root-to-first-stage.yaml
    └── 001-first-stage-to-next-stage.yaml
```

Use a monotonically increasing sequence and stable stage names. The run-state file indexes the
current validated input and latest produced contract; it does not replace either contract. Final
outputs must be traceable through contract evidence locators to durable artifacts.

## Failure and Recovery

- **Invalid input:** do not start work; return validation issues with exact remediation.
- **Missing information:** record an open question, retrieve only when authorized, otherwise block.
- **Contradictory evidence:** preserve both claims and evidence, record the contradiction, and route
  to an allowed resolution stage or stop as `blocked`.
- **Partial completion:** use `partial`, list unmet criteria and a precise continuation point, and
  redispatch the same stage when safe. Do not advance to a different stage.
- **Tool or artifact failure:** record the dependency, error category, attempted action, and safe
  retry or escalation condition. Never invent a result.
- **Changed artifact:** when a digest is present, a mismatch requires revalidation. Intentional
  evolution creates a new artifact identifier and digest rather than mutating inherited evidence.
- **Workflow conflict:** the workflow wins unless an authorized, versioned amendment says otherwise.
- **Blocked or failed work:** checkpoint the status and route only as the workflow permits.

User approval gates remain authoritative. A contract may reference recorded approval evidence but
must never infer approval.
