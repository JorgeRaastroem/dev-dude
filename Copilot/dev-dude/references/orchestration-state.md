# Durable Orchestration State

This contract applies to every DevDude command. The root skill owns state transitions; functional
workflow skills own only the work inside their declared entry and exit states.

## State Location

- Architecture: `./docs/ArchOverview/.dev-dude-run-state.md`
- Feature: `./docs/<feature-slug>/.dev-dude-run-state.md`

Create the parent output directory and state file before delegating the first task. Preserve the
state file when cleaning `.tmp/` artifacts and after completion so a later session can explain or
resume the run.

## Required State

Keep the file concise and update it in place using this structure:

```markdown
# DevDude Run State

- **Command**: <normalized command and argument>
- **Workflow**: <architecture|feature>
- **Workflow version**: <workflow definition or amendment version>
- **Run ID**: <stable run identifier>
- **Status**: <active|waiting-for-user|complete|bounded-unresolved|cancelled|abandoned>
- **Current block**: <installed functional skill name>
- **Current step**: <step identifier and name>
- **Validated input contract**: <path under .dev-dude-handoffs/>
- **Latest output contract**: <path under .dev-dude-handoffs/ or none>
- **Next transition**: <one permitted next action>
- **Source revision**: <git HEAD when last reconciled, or unavailable>
- **Updated**: <ISO-8601 timestamp>

## Gates
| Gate | Status | Decision evidence |

## Tasks
| ID | Owner | Status | Expected output | Evidence |

## Reconciliation
- <checks performed and discrepancies found>

## Temporary Artifacts
- **Output directory**: <./docs/ArchOverview/|./docs/<feature-slug>/>
- **Run-owned temporary directory**: <output-directory>/.tmp/
- **Durable outputs**: <final paths or none>
- **Validation evidence**: <paths/results or not-yet-final>
- **Decision**: <preserve-for-resume|cleanup-authorized|cleanup-complete|cleanup-failed>
- **Decision evidence**: <normal-completion checks or explicit user decision>
- **Cleanup result**: <not-attempted|absent|removed|exact failure and remediation>
```

Allowed run statuses are `active`, `waiting-for-user`, `complete`, `bounded-unresolved`, `cancelled`,
and `abandoned`. Allowed task statuses are `pending`, `running`, `complete`, `failed`, and
`superseded`. Record user decisions by concise quotation or by a durable document path; do not infer
approval.

## Checkpoint Rules

Update state:

1. before delegating a task (`pending` then `running`);
2. after every task result, including failures;
3. before and after every user gate;
4. when entering or exiting a functional workflow block;
5. after each validation/remediation attempt; and
6. before reporting completion or bounded unresolved work.

Write the checkpoint before starting the next transition. A checkpoint records orchestration facts,
not investigation content; detailed findings stay in normal workflow outputs.

## Temporary Artifact Lifecycle

This is the single cleanup rule for every architecture and feature workflow. Functional skills may
produce or consume temporary evidence, but the root orchestrator owns preservation and cleanup.

1. Scope temporary evidence to the current workflow output directory: architecture uses
   `./docs/ArchOverview/.tmp/`; a feature uses `./docs/<feature-slug>/.tmp/`. Record the exact output
   and temporary paths plus evidence that the current run owns that `.tmp/`. If ownership is unclear,
   preserve it and stop at a user gate.
2. Preserve the entire run-owned `.tmp/` while any pending or running task, current or future stage,
   transition contract, validation/remediation attempt, or user gate references an artifact inside
   it. A normal interruption preserves it for reconciliation and resume. A `bounded-unresolved`
   terminal result also records `preserve-for-resume` and keeps `.tmp/`; cleanup requires a later
   explicit cancellation or abandonment decision.
3. After successful workflow completion, cleanup is authorized only after:
   - every final output and exit/transition contract is present and validated;
   - a pre-cleanup checkpoint records `complete`, all durable output paths, validation evidence, and
     `cleanup-authorized`; and
   - the latest terminal contract and checkpoint resolve final evidence only through durable paths,
     not `.tmp/`; and
   - reconciliation confirms that no pending task, stage, gate, or current contract references
     `.tmp/`. Immutable historical contracts may retain their original temporary locators as audit
     history after their consuming transitions are complete.
4. Delete only the recorded run-owned `.tmp/` directory. Never delete
   `.dev-dude-run-state.md`, `.dev-dude-handoffs/`, final documents, the output directory itself, a
   symlink, a resolved path other than the expected `.tmp/` child, or any unrelated temporary
   directory. Do not use a wildcard, parent-directory sweep, or repository-wide cleanup.
5. Cleanup is idempotent: an already absent recorded `.tmp/` is success. After every attempt,
   checkpoint `absent` or `removed` with evidence. If deletion fails, leave the substantive run
   `complete`, record `cleanup-failed`, the exact error, remaining path, and a safe remediation
   action, and do not broaden the deletion scope.
6. On explicit cancellation or abandonment, stop new dispatches, cancel or join every running worker,
   and confirm they are quiescent before terminalization. At a user gate, ask whether to preserve
   `.tmp/` evidence for resume or clean it up and record the quoted decision. Mark every incomplete
   task `superseded`, then validate and checkpoint the terminal cancellation or abandonment contract,
   retained durable outputs, available validation evidence, and artifact decision. Preservation ends
   with `preserve-for-resume`; a later explicit resume reconciles the preserved evidence and creates
   a new root-to-stage contract without mutating the terminal contract. For cleanup, additionally
   confirm no remaining stage reference, then apply the same narrow, idempotent deletion rule.

### Lifecycle Conformance Examples

| Scenario | Required result |
|---|---|
| Successful completion | Validate final outputs/contracts, checkpoint durable paths and evidence, confirm no pending `.tmp/` reference, remove only the recorded `.tmp/`, then checkpoint the result. |
| Paused user gate | Keep `.tmp/` intact, set `waiting-for-user`, and record the gate; do not authorize cleanup. |
| Resumable interruption | Preserve `.tmp/`, reconcile it on entry, and continue from the first incomplete step. |
| Bounded unresolved | Record the remaining remediation and `preserve-for-resume`; clean only if a later cancellation or abandonment gate authorizes it. |
| Explicit abandonment | Ask preserve-or-clean, record the decision, and clean only after terminal reconciliation if the user selects cleanup. |
| Repeated cleanup | Treat a missing recorded `.tmp/` as successful and checkpoint `absent` without touching any other path. |

Every transition contract is a YAML file under `.dev-dude-handoffs/` beside this state file. Keep
validated contracts immutable; remediation creates the next sequenced contract. The state file
indexes the current validated input and latest output. Read
[stage-workflow.md](stage-workflow.md), [handoff-contract-schema.md](handoff-contract-schema.md), and
[validation-rules.md](validation-rules.md) before creating, consuming, or validating a contract.

## Reconciliation and Recovery

On every command entry, stage entry, direct resume, or suspected compaction:

1. Read this contract and the run-state file.
2. Inspect the expected output paths, current repository changes, and relevant approval or
   verification documents.
3. Reconcile every `running` or `complete` task:
   - An output-backed task is complete only when its expected output exists and contains the
     completion evidence required by its functional workflow.
   - A code-changing task also requires its result summary and the expected repository changes.
   - Missing or stale evidence moves the task to `pending`; record why.
   - Evidence of completed work may advance a stale checkpoint; record the discovered evidence.
4. Never roll back, overwrite, or repeat valid work solely because the checkpoint is stale.
5. Validate the current contract and reconcile its evidence and artifact references. A stale or
   invalid contract does not authorize a transition; record structured remediation.
6. Determine exactly one valid next transition from reconciled evidence and update state.
7. Initialize a fresh stage with only its workflow, validated contract, authorized artifacts/tools,
   and current-stage tool results, then continue from its first incomplete step.

The filesystem and repository are evidence; the state file is the index. If they disagree and the
safe transition is unclear, set `waiting-for-user`, record the discrepancy, and ask at a gate.

## Orchestration Envelope

Every delegated task prompt must contain this compact envelope before task-specific context:

```markdown
## DevDude Orchestration
- Run state: <path>
- Workflow block: <installed skill name and step>
- Task ID: <stable ID matching the state table>
- In lane: <single responsibility for this task>
- Expected output: <path or result contract>
- Completion evidence: <specific evidence required>
- Input handoff: <validated YAML contract path>
- Output handoff: <next YAML contract path>
- Next owner: root DevDude orchestrator
```

Also include only the context blocks authorized by the input contract. An agent must not use prior
conversation as workflow state, advance the workflow, change gate status, or assume work owned by
another block; it returns control and a typed evidence contract to the root orchestrator.
