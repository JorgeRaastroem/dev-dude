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
- **Status**: <active|recovery-paused|waiting-for-user|complete|bounded-unresolved>
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

## Watchdog
| Action ID (task/step/tool) | Parent invocation | Mode and verified capabilities/limitations | Started (UTC) | Deadline (UTC) | Last check (UTC) | Retries (0-3) | Invocation ID | Execution status and evidence | Outcome |

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
5. after each validation/remediation attempt;
6. at each watchdog check, deadline exceeded, execution-status change, cancellation request, and retry; and
7. before reporting completion or bounded unresolved work.

Write the checkpoint before starting the next transition. A checkpoint records orchestration facts,
not investigation content; detailed findings stay in normal workflow outputs.

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
   - Establish whether its invocation and descendants are still active, completed, or verified
     stopped. Missing outputs, a stale journal, or an elapsed deadline do not establish termination.
     If active, monitor without redispatch; if unknown, record `execution status unknown`, set
     `recovery-paused`, and pause recovery until completion or verified termination is established.
   - An output-backed task is complete only when its expected output exists and contains the
     completion evidence required by its functional workflow.
   - A code-changing task also requires its result summary and the expected repository changes.
   - Missing or stale evidence moves the task to `pending` only after its invocation and descendants
     are confirmed quiescent; reconcile partial outputs and side effects first and record why.
   - Evidence of completed work may advance a stale checkpoint; record the discovered evidence.
4. Never roll back, overwrite, or repeat valid work solely because the checkpoint is stale.
5. Validate the current contract and reconcile its evidence and artifact references. A stale or
   invalid contract does not authorize a transition; record structured remediation.
6. Determine exactly one valid next transition from reconciled evidence and update state.
7. Only after prior work and descendants are confirmed quiescent, initialize a fresh stage with only
   its workflow, validated contract, authorized artifacts/tools, and current-stage tool results,
   then continue from its first incomplete step within the persisted retry budget.

The filesystem and repository are evidence; the state file is the index. Execution uncertainty
alone uses `recovery-paused`. If discrepancies reveal safety concerns, uncertain side effects,
conflicting work, or scope changes, set `waiting-for-user`, record the discrepancy, and ask at a gate.

## Watchdog

The root owns monitoring for functional-skill dispatches; each functional skill owns it for
delegated agents, external tools, and shell commands within its stage. Select and record a mode
per invocation based on verified capabilities, not assumptions about a background wrapper:

- **Controlled mode:** verify a usable control mechanism for this specific invocation: either
  background execution with bounded status polls and cancellation callable while work is active,
  or a runtime-enforced timeout returning control within the check interval. A cancellation tool
  alone is insufficient if the invocation prevents monitoring or calling it. Retain the verified
  mechanism. Request cancellation or let the enforced timeout act at the deadline
  if still active. Verify termination of the invocation and descendants before recovery.
- **Cooperative mode:** neither usable control mechanism is verified for this invocation, even if
  the runtime advertises cancellation elsewhere. Dispatch through the runtime's supported
  invocation mechanism, including synchronous calls when necessary; do not require user approval
  merely because cancellation is unavailable. Record the limitation before launch. Instruct work to
  stay within its bounded objective, checkpoint progress through its owner, and return partial or
  blocked results with a continuation point when appropriate. Deadlines are monitoring thresholds,
  not guaranteed interruption. Cooperative monitoring cannot guarantee interruption or bounded
  return time; prompts cannot interrupt a hung synchronous call.

Prefer background execution and bounded polls when supported. In cooperative synchronous execution,
root may be unable to check while the call is active; the stage checkpoints its journal as control
permits, and root reconciles on return or resume. Do not promise a check cadence the runtime cannot
provide. User-decision gates are not timed or retried. Genuine safety concerns, uncertain side
effects, conflicting work, and scope changes still require an explicit gate.

## Single-writer and nested actions

Only root writes `.dev-dude-run-state.md`, including task/gate transitions and the consolidated
watchdog table. For each stage invocation, root assigns an invocation ID and a stage-owned journal
at `<run-output>/.dev-dude-watchdog/<invocation-id>.md`, and passes its path to that stage. The stage
is the sole writer of its journal; it never edits the run state. Before dispatch and after each
check/result, the stage records its own status and last update, plus each child action's parent ID,
invocation ID, mode and capabilities/limitations, start/deadline, retry count, last check,
execution status, outcome, and evidence in its journal.
Root reads the journal at every available check or return and copies reconciled facts into the run
state; missing, stale, or conflicting journal data cannot prove a child stopped. Delegated agents
report results to their stage owner and never edit
either file. Checkpoint instructions within a functional workflow mean write the stage journal
and let root reconcile it into run state. Preserve journals across resumes until all referenced
invocations are quiescent and their evidence is indexed in the run state. A restarted stage reads
prior journals and the run state for that action ID before choosing a retry count; a new stage
invocation ID never resets an action's retry budget.

Root's deadline applies to the stage invocation, not independently to its child actions. Each
child has its own mode, deadline, and retry budget in the stage journal. Root may request cancellation
of a deadline-exceeded stage in controlled mode only after examining its journal; confirm both the
stage and all descendants have completed or are verified stopped before redispatch. If any may
remain active, do not retry, launch replacement work, advance the stage, or allow overlapping writes
(including cleanup of their artifacts). Unknown status pauses recovery, not initial dispatch; user
approval alone is not termination evidence. A gate requested by a stage is not a running invocation:
the stage returns a `blocked` handoff and stops, then root validates it, records
`waiting-for-user`, and asks without a deadline. The next invocation starts only after explicit
decision evidence and a new validated same-stage handoff.

Before each action, assign a stable action ID (task ID, step, and tool/action), record its start,
mode and capabilities/limitations, deadline, invocation identifier if available, and retry count in
its owner's file (run state for root actions, stage journal for child actions). Default to a
60-second check interval and a 10-minute deadline per attempt. For an action expected to need
longer, record a justified deadline *before* starting it; never extend a running attempt's
deadline merely because it is still running. Start a new deadline for each retry, preserving the
same action ID and retry count across resumes. Where the runtime supports polling, use bounded waits
of at most 60 seconds and check each concurrent action at least every 60 seconds. Otherwise record
the unavailable live monitoring and reconcile as soon as control returns.

At each check, read the run state, stage journal when applicable, and validated input handoff;
restate the current step's objective, completion evidence, and permitted next transition, then
reconcile completed results with actual
outputs and repository changes. Record the check time and evidence. If an action is still active
before its deadline, continue bounded polling; a completed action follows normal contract
validation. A missing or invalid handoff blocks progress, never authorizes an inferred next step.

At or on the first available check after the deadline, record `deadline exceeded` separately from
execution status. If still active in controlled mode, request cancellation of the specific
invocation (or let its enforced timeout act), then verify termination; a request is not proof it stopped.
In cooperative mode, continue monitoring a known active invocation without retrying it. If status
cannot be established in either mode, record `execution status unknown` with the available evidence
and set `recovery-paused`; do not mark the task failed or cancelled merely because time elapsed.
Record `verified stopped` or `completed` only with evidence covering the invocation and descendants
(runtime status/result references or other verified termination evidence, not missing artifacts).
Never mark an invocation cancelled without verified cancellation evidence.

Resume recovery only after completion or verified termination of all prior work. Reconcile partial
outputs and side effects before deciding whether the action remains incomplete; validate a complete
result normally even if its deadline was exceeded. Retry only the same incomplete
action when it is safe to repeat, up to **three retries after the initial attempt**, recording
each attempt before dispatch. Do not replay completed work, non-idempotent side effects, or an
action whose prior invocation or descendants may still be running. If status is unknown, the stage
reports the uncertainty in its journal and root pauses recovery; no user approval is needed solely
for the missing cancellation capability. If a safe repeat cannot be established because of genuine
safety concerns, uncertain side effects, conflicting work, or scope changes, root sets
`waiting-for-user` and asks at a gate with the evidence. Approval never bypasses the quiescence check.
After the third failed retry, the action owner records exhaustion (root in run state, stage in its
journal); root marks the task failed and the run `bounded-unresolved`, recording the failure and
exhausted budget. Do not
advance to another stage. The watchdog retry budget is
independent of the feature validation/remediation attempt counter. On resume, reconcile evidence
and reuse the persisted count; never reset it to evade exhaustion.

## Orchestration Envelope

Every delegated task prompt must contain this compact envelope before task-specific context:

```markdown
## DevDude Orchestration
- Run state: <path>
- Workflow block: <installed skill name and step>
- Task ID: <stable ID matching the state table>
- Execution mode: <controlled|cooperative; verified capabilities and limitations>
- Monitoring deadline: <UTC threshold; not a guaranteed stop in cooperative mode>
- Progress reporting: <return checkpoints/results to stage owner; stage journal path for stages>
- In lane: <single responsibility for this task>
- Expected output: <path or result contract>
- Completion evidence: <specific evidence required>
- Input handoff: <validated YAML contract path>
- Output handoff: <next YAML contract path>
- Next owner: invoking functional stage (root only for a stage output handoff)
```

Also include only the context blocks authorized by the input contract. An agent must not use prior
conversation as workflow state, advance the workflow, change gate status, or assume work owned by
another block; it returns control and typed evidence to its invoking stage. The stage reconciles
child results into its journal and returns its output handoff for root to validate.
Stay within the bounded objective and report partial or blocked results with unmet criteria and a
continuation point when appropriate. Report any still-active descendants; a returned result alone
does not prove descendant termination.
