# Durable Orchestration State

This contract applies to every DevDude command. The root skill defines state transitions, executed
by the dedicated DevDude orchestrator agent. In all supplied workflow documents, **root** means
that dedicated controller, not the invoking host. Functional workflow skills own only the work
inside their declared entry and exit states.

The host installs/verifies prerequisites and relays controller results. It never writes run
outputs, state, journals, or handoffs, reconciles stage results, or selects transitions. When root
"asks the user", it checkpoints the gate and returns a structured `blocked` result with the exact
question/options for the host to relay. The host passes the user's verbatim decision as evidence
to the next controller invocation; only root validates and records it. No human wait occurs inside
an active controller or stage invocation.

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
- **Orchestrator invocation**: <correlation ID; runtime invocation ID or unavailable; started UTC; last update UTC; execution status and evidence; mode and verified capabilities/limitations>
- **Heartbeat**: <backend or unavailable; job identity; interval; verified limitations; latest host check UTC and evidence, or none>
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

On controller entry, verify identity and capabilities from the host bootstrap packet, then reconcile
prior invocation and descendant quiescence before claiming sole-writer ownership. Record the new
controller invocation in run state before dispatching any functional stage; update it at available
checks and before returning to the host. Preserve its correlation ID even when runtime IDs are
unavailable. Existing state without this field remains resumable, but the absence never proves
quiescence: inspect task records, journals, and available runtime evidence before continuing.

The host may read this marker and runtime results to prevent duplicate dispatch, but never writes
it. A stale `active` checkpoint is not a permanent lock, and a `waiting-for-user`, `complete`, or
`bounded-unresolved` label is not termination evidence. If the prior controller or descendants
remain active, monitor without replacement; if status is unknown, report recovery paused without
dispatching another controller. Root records `recovery-paused` when it has control. Controller
returns include descendant identities and status evidence; a parent return alone cannot establish
quiescence. Quiescence must be established before recovery even after user approval.

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

## Host Heartbeat

The action watchdog above runs only while its owner has control. A separate **host-owned heartbeat**
wakes the host after unrelated scheduled work, context compaction, or an interrupted controller
return. It checks run and runtime state, not whether chat has been quiet. It never performs stage
work, chooses a transition, writes run outputs, or cancels an invocation merely because it is stale.
Keep the existing 60-second action checks and per-action deadlines; this heartbeat is a distinct
five-minute recovery check, configurable between five and ten minutes.

### Scheduler Options

Select from capabilities actually exposed by the installed runtime; a prompt cannot create a timer.

| Option | Quiet operation and recovery | Limits / selection |
|---|---|---|
| Native recurring host prompt | Preferred for a live session: one short read-only check every five minutes; no healthy-check reply | Verify scheduling, list/delete, job lifetime, and behavior when busy or compacted. Claude Code offers `/loop` / cron tools where exposed; discover Copilot scheduling capabilities rather than inventing a command. Queued prompts cannot guarantee checks while the host is blocked. |
| External local supervisor (OS timer or approved scheduler integration) | Best option when checks must continue independently of a busy/closed session; poll status quietly and wake the host only for recovery | Requires user-approved setup, access to the same checkout and verified controller/descendant status, and serialized dispatch. A timer alone does not provide runtime observability or safe session attachment. Do not install a service, change permissions, or launch another CLI session automatically. |
| Resume/compaction hooks | Cheap supplementary check on re-entry; no idle polling or repeated replies | Runtime-specific, permission-gated, and event-driven only: cannot satisfy a five-to-ten-minute cadence by themselves. |
| GitHub Actions schedule | Suitable only for a workflow whose state, outputs, and runtime control live in that runner environment | Not a watchdog for a local CLI: separate checkouts cannot observe local invocations or uncommitted checkpoints; scheduled runs can be delayed. Do not add a repository schedule for local recovery. |

Runtime references: [Claude Code scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks),
[Copilot CLI command reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference),
and [GitHub Actions schedule limitations](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
Recheck installed capabilities rather than assuming these surfaces or persistence are universal.
If the scheduler cannot check while another turn runs, record **best-effort session heartbeat**,
not guaranteed five-to-ten-minute monitoring. If independent monitoring is required but unavailable,
offer an explicit setup gate for an external supervisor; manual re-entry remains safe but is not a timer.

### Registration and Ownership

1. The host prepares a scheduler descriptor before controller dispatch and passes it in the bootstrap
   packet. Bind one job to the canonical repository root, stable Run ID, absolute run-state locator,
   installed root skill locator, and original command/input locators. For a new run, wait for the
   controller's first published checkpoint before arming the job; never guess a run or create state.
2. Store the job binding and last-check observation in the runtime/scheduler's own metadata, not a
   host-written file under the run output. Root alone records the `Heartbeat` field from supplied
   evidence at its next available checkpoint. Missing heartbeat metadata in older state is supported.
3. On host resume or compaction, rediscover the bound job and verify its cadence, lifetime, and
   capability limitations; reuse it, or replace a verified expired/missing job. Unknown job identity
   blocks duplicate registration. Never delete unrelated schedules or assume conversation preserves
   a timer. A session-scoped job cannot recover a closed session without an external supervisor.
4. Serialize all host dispatches for this run, including ordinary commands and user-gate resumes,
   using a verified exclusive runtime dispatch mechanism or run-keyed lock outside run outputs.
   Hold it through the status check and publication of the new controller identity; re-read state
   and runtime evidence after acquiring it. A competing or unverifiable lock skips dispatch, never
   authorizes bypass. Installation usage locks from host bootstrap remain required.
5. Verify scheduler permission before registration. A permission failure stops at a setup gate;
   do not switch backend or install hooks/services as a workaround. Unsupported scheduling alone
   does not block ordinary workflow execution: report the limitation once.

For a native recurring prompt, use a five-minute interval (or `*/5 * * * *` where POSIX cron is
supported) with a compact, self-contained payload:

```text
DevDude host heartbeat; not an orchestrator or a new workflow command.
Repository: <canonical absolute root>; Run ID: <bound ID>; state: <absolute locator>.
Installed root skill: <absolute SKILL.md>; original command/inputs: <bound locators>.
Read the root's host-heartbeat policy and perform one read-only wake-up check.
No reply for healthy/unchanged state. Re-enter only through host bootstrap after verified
controller/descendant quiescence and serialized dispatch; preserve gates and retry budgets.
```

The timer payload is a locator packet, not approval or workflow authority. Retain an explicit stop
in the scheduler binding until authorized continuation; never infer renewed consent from old state.

### Each Wake-up

Perform one bounded read-only check of the bound checkpoint, controller runtime status, descendant
status/journals, and latest handoff locator. Revalidate repository and Run ID; a missing, malformed,
replaced, or mismatched binding never authorizes creating or resuming a different run.

| Observed condition | Host action |
|---|---|
| Explicit user stop, `waiting-for-user`, `complete`, or `bounded-unresolved` (check first) | Suspend/remove only the bound recovery job; never auto-approve a gate or restart terminal work. These labels still do not prove termination or permit cleanup/lock release. |
| Controller or any descendant is active | No replacement or cancellation; keep monitoring quietly, even if the checkpoint is stale. |
| Controller/descendant status is unknown, or binding/status evidence is missing | No dispatch; report recovery paused once, retain checks for new evidence. Root records `recovery-paused` only when it has control. |
| Prior controller and every descendant are completed or verified stopped; run is incomplete and not gated/stopped | Under the serialized dispatch check, re-enter the same dedicated controller through host bootstrap with durable locators, original inputs, and status evidence. Root reconciles outputs, journals, approvals, repository changes, and validated contracts before selecting the first incomplete step. |

An interrupted or missing result may use this recovery path only after verified quiescence; a failed
result is not permission to bypass remediation or an exhausted budget. Preserve Run ID, completed
work, immutable handoffs, action retry counts, and validation counters. Neither a heartbeat tick nor
a new controller resets a budget. Unknown side effects, conflicts, or scope changes require the
existing safety gate. Re-arm a suspended job only on explicit authorized continuation.

Healthy checks and unchanged paused/gated conditions produce **no conversational reply** or repeated
objective/status narration. Keep one latest check timestamp/outcome/evidence in scheduler metadata,
not an append-only tick transcript. Emit a short notice only on recovery dispatch, a new blocker or
gate, scheduler loss, or completion; deduplicate unchanged notices. Runtime tool/schedule UI may
still be visible: promise quiet responses, not invisible tool execution. If a check is delayed past
ten minutes, record the missed cadence and limitation at the next opportunity instead of claiming
continuous coverage or replaying missed ticks.

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

Every stage or specialist task prompt must contain this compact envelope before task-specific
context. The host-to-controller bootstrap packet is separate: root has not yet initialized or
reconciled state and cannot supply a validated stage contract until it takes control.

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

Also include only the context blocks authorized by the input contract. A specialist agent must not use prior
conversation as workflow state, advance the workflow, change gate status, or assume work owned by
another block; it returns control and typed evidence to its invoking stage. The stage reconciles
child results into its journal and returns its output handoff for root to validate.
Stay within the bounded objective and report partial or blocked results with unmet criteria and a
continuation point when appropriate. Report any still-active descendants; a returned result alone
does not prove descendant termination.
