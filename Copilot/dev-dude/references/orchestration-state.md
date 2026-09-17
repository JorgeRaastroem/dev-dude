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
- **Status**: <active|waiting-for-user|complete|bounded-unresolved>
- **Current block**: <installed functional skill name>
- **Current step**: <step identifier and name>
- **Next transition**: <one permitted next action>
- **Source revision**: <git HEAD when last reconciled, or unavailable>
- **Updated**: <ISO-8601 timestamp>

## Gates
| Gate | Status | Decision evidence |

## Tasks
| ID | Owner | Status | Expected output | Evidence |

## Reconciliation
- <checks performed and discrepancies found>
```

Allowed task statuses are `pending`, `running`, `complete`, `failed`, and `superseded`. Record user
decisions by concise quotation or by a durable document path; do not infer approval.

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

## Reconciliation and Recovery

On every command entry, phase entry, direct resume, or suspected compaction:

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
5. Determine exactly one valid next transition from reconciled evidence and update state.
6. Load only the current functional workflow reference, then continue from its first incomplete
   step.

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
- Next owner: root DevDude orchestrator
```

Also include the context blocks required by the functional workflow. An agent must not advance the
workflow, change gate status, or assume work owned by another block; it returns control and evidence
to the root orchestrator.
