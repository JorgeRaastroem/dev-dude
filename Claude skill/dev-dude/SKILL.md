---
name: dev-dude
description: >
  Resumable architecture investigation and feature implementation using agent swarms.
  DudeWhereIsMyArch (arch/where) writes architecture docs to ./docs/ArchOverview/.
  DudeWriteMyFeature (feature/write) accepts descriptions, specs, or images and writes design,
  implementation, and verification outputs to ./docs/<feature-slug>/.
---
argument-hint:
  - "DudeWhereIsMyArch all" — Full architecture investigation
  - "all refresh" — Refresh affected architecture docs
  - "authentication refresh" — Refresh one architecture vertical
  - "DudeWhereIsMyArch authentication" — Investigate one area
  - "DudeWriteMyFeature Add user caching" — Design and implement a feature

# DevDude Root Orchestrator

This root skill defines setup, routing, durable state, user gates, and functional workflow
transitions. The dedicated `dev-dude-orchestrator` agent executes that orchestration;
the invoking host only bootstraps and relays user decisions. Neither performs specialist work.
Agent definitions supply orchestration expertise; this skill and its references supply workflow
authority. A general-purpose agent must never substitute for the dedicated controller.

## 1. Host Bootstrap — Prepare the Runtime

This section is host-only. An already-selected orchestrator receiving `entry_role: orchestrator`
must skip it and start at section 2; it must never invoke itself or another controller.

### Install and Verify the Agent Crew

Bundled agent crew version: `1.0.5`. Compare the `version:` frontmatter of all bundled agents with
project-local and global `.claude/agents/` installs. Missing version is `0`. If any agent is missing
or older, update the complete crew atomically; preserve an equal or newer installed crew.

Required Task `subagent_type` values:

- `dev-dude-orchestrator`
- `code-flow-analyzer`
- `ux-design-reviewer`
- `architecture-reviewer`
- `technical-resource-investigator`
- `investigation-documenter`
- `feature-implementer`
- `test-implementer`
- `feature-validator`

### Install and Verify the Functional Skill Crew

Bundled skill crew version: `1.1.3`. Bundled directories under `skills/`:

- `dev-dude-architecture`
- `dev-dude-feature-design`
- `dev-dude-feature-implementation`
- `dev-dude-validation`

Install them as sibling skills alongside the active root:

- project root at `<repo>/.claude/skills/dev-dude/` → `<repo>/.claude/skills/<skill-name>/`
- user root at `~/.claude/skills/dev-dude/` → `~/.claude/skills/<skill-name>/`

For each installed `SKILL.md`, compare its top-level `version:` with the bundled version. Missing
skill or version is `0`.

- If every installed version equals the bundle, keep the crew.
- If none is newer and any is missing or older, copy all four bundled directories to a staging
  directory under the target, verify every staged name/version, then replace all four installed
  directories only after staging succeeds. Remove staging on failure and leave the installed crew
  unchanged.
- If any installed version is newer while another is missing or older, stop at a version-conflict
  gate rather than mixing versions or silently downgrading.
- If every installed version is equal to or newer than the bundle, preserve the installed crew and
  report newer versions.

Verify all four names are discoverable through the Skill capability before dispatch. If copying or
discovery fails because of permissions, stop at a **FUNCTIONAL SKILL INSTALL GATE**, report the exact
target and failure, and ask the user before trying any alternative location or method.

Confirm `TeamCreate` is available. If not, stop with remediation. Install Mermaid CLI
(`npm install --global @mermaid-js/mermaid-cli`) or require the documenter to report use of an
available parser fallback.

### Build Session Context

1. Detect available code-indexing MCP servers. At least one is required. If several are available,
   ask the user to select; auto-select a sole indexer. Run its onboarding when needed.
2. Build `$INDEXER_CONTEXT` with each selected indexer's prefix, search, symbol, modification, and
   memory capabilities. Load relevant project memories.
3. Separately detect documentation MCP, GitHub/registry lookup, and WebFetch/WebSearch tools. Build
   `$RESOURCE_RESEARCH_CONTEXT` and bind it to
   [trusted-source-policy.md](references/trusted-source-policy.md). If reliable external research is
   unavailable, record that and require repository-local investigation only.

If a critical prerequisite fails, report remediation and stop.

### Transfer Control to the Dedicated Agent

Verify `dev-dude-orchestrator` is discoverable as a custom agent. Verify its invocation can access
Skill, delegate nested specialist tasks, use TeamCreate, and write the authorized run outputs.
Host-level tool availability is not evidence of child access; use runtime capability metadata, or
let the selected agent verify its exposed capabilities before any workflow action. If unsupported
or unknown, stop at an **ORCHESTRATOR CAPABILITY GATE** with exact remediation. Permission failures
require user approval before any alternative method or location; never fall back to general-purpose.

Read existing run state and controller/descendant runtime status only to prevent duplicate
dispatch. An `active` checkpoint may be stale: dispatch recovery only with evidence the prior
controller and descendants completed or are verified stopped, regardless of its recorded status.
If still active, monitor without replacement; if unknown, report recovery paused and stop.
Missing output files, elapsed deadlines, and user approval never establish quiescence.

Invoke Task with `subagent_type: dev-dude-orchestrator`, using supported background execution or
cooperative synchronous execution. Pass a compact bootstrap packet, not a restatement of the
agent's responsibilities:

- `entry_role: orchestrator`, a unique controller invocation correlation ID, and repository root;
- the absolute path of this root `SKILL.md`, original command and input paths;
- absolute shared-policy paths under this root's `references/`;
- authorized `$INDEXER_CONTEXT`, `$RESOURCE_RESEARCH_CONTEXT`, and verified runtime capabilities;
- existing run-state/latest-contract locators when known, or `none` for a new run;
- explicit user decision evidence, quoted verbatim, when resuming a gate.

This packet transfers control; it is not a stage handoff and cannot authorize a stage transition.
The controller creates and validates normal stage contracts after reconciliation. The host never
writes run outputs, state, journals, or handoffs and never chooses workflow transitions.
Monitor the controller using the verified mode; do not claim cancellation without evidence.
On a `blocked` result, relay its exact question/options to the user without a deadline. Pass the
verbatim response back through this bootstrap only after prior work is quiescent. On `partial`,
relay the continuation; on `failed` or malformed/missing results, report the failure and stop, never
take over. On `complete`, report the returned evidence. Every subsequent entry uses this same
dedicated agent, reconciling durable evidence rather than passing conversation history.

## 2. Orchestrator Entry — Route the Command

Sections 2–6 are executed only by the dedicated controller. Verify the bootstrap entry role,
identity, and required child capabilities before starting. After locating and reconciling run state,
record the controller invocation identity and verified execution capabilities under
[orchestration-state.md](references/orchestration-state.md). If the bootstrap packet is invalid,
return `blocked` with remediation; do not execute host bootstrap or specialist work.

Normalize arguments in this order:

1. Exactly two tokens ending in `refresh` route to Architecture Delta Refresh; reject multi-token
   refresh scopes.
2. `DudeWhereIsMyArch`, `arch`, or `where` route to Architecture Investigation.
3. `DudeWriteMyFeature`, `feature`, or `write` route to Feature Design & Implementation.
4. Otherwise print usage and stop.

Architecture accepts `all`, an area, a directory, or `<all|vertical> refresh`. Feature accepts text,
`.md`, `.txt`, `.docx`, `.pdf`, image paths, or multiple paths. Derive a lowercase, hyphenated
feature slug of at most 40 characters.

## 3. Recover or Initialize State

Read [orchestration-state.md](references/orchestration-state.md) and
[stage-workflow.md](references/stage-workflow.md) on every command entry, stage entry, direct resume,
or suspected compaction. Load [handoff-contract-schema.md](references/handoff-contract-schema.md) and
[validation-rules.md](references/validation-rules.md) whenever creating or validating a transition.

- Architecture state: `./docs/ArchOverview/.dev-dude-run-state.md`
- Feature state: `./docs/<feature-slug>/.dev-dude-run-state.md`

Create state before the first delegated task. If state exists, reconcile it with actual outputs,
task results, repository changes, and gate evidence before choosing a transition. Update it before
and after every task, gate, workflow-block transition, and validation attempt.

## 4. Dispatch Functional Workflows

| Reconciled condition | Load and execute |
|---|---|
| Architecture run is incomplete | Invoke `dev-dude-architecture` at its first incomplete step |
| Feature design is not explicitly approved | Invoke `dev-dude-feature-design` at its first incomplete step |
| Feature design is approved but implementation/test evidence is incomplete | Invoke `dev-dude-feature-implementation` |
| Implementation and paired-test evidence is complete | Invoke `dev-dude-validation` |
| Validation requests production/test remediation | Invoke the named implementation skill, then `dev-dude-validation` |
| Feature clarification changes the design materially | Supersede the implementation attempt and create a new root-validated design input contract for `dev-dude-feature-design`; require renewed approval |
| Workflow exit contract is met | Record final status and report |

Treat each functional-skill dispatch as a fresh, bounded stage. At each dispatch:

1. Declare the stage objective, inputs, outputs, completion criteria, and one permitted transition.
2. Create or select its YAML input contract and run the contract validation gate. Do not dispatch on
   failure; return structured remediation.
3. Invoke the installed functional skill by name through the Skill capability with no prior-stage
   conversation history using the runtime's supported invocation mechanism. Select controlled mode
   only when this invocation supports background execution with bounded status polls and callable
   cancellation, or an enforced timeout returning control within the check interval; otherwise
   select cooperative mode and
   record its limitations before dispatch. Missing cancellation alone is not a prerequisite failure
   or approval gate. Do not assume a background Task wrapper can cancel Skill or its descendants.
4. Pass only its workflow definition, validated contract, explicitly authorized artifacts and tools,
   state and stage-journal paths, shared-policy paths, handoff schema and validation-rule paths,
   and the orchestration envelope.
5. Pass `$RESOURCE_RESEARCH_CONTEXT` only when authorized for `dev-dude-feature-design`.
6. Require a typed output contract containing completion evidence and returning control to root.
7. Validate, reconcile, and checkpoint that contract before any next dispatch. `partial`, `blocked`,
   or `failed` work cannot advance to a different stage.

Apply the watchdog in [orchestration-state.md](references/orchestration-state.md) while the
functional skill runs in its selected mode. Checkpoint its invocation and monitor against the
validated handoff and run state as the runtime permits; preserve bounded polls in controlled mode.
Cooperative deadlines are monitoring thresholds, not guaranteed interruption or bounded return
time. Record `deadline exceeded` separately from `execution status unknown` and `verified stopped`;
never claim cancellation without evidence. Pause recovery, not initial dispatch, when prior work
may still be active. Do not retry, replace work, or permit overlapping writes until the invocation
and descendants have completed or are verified stopped; reconcile partial outputs first.
Root alone writes run state and reconciles the stage-owned journal at available checks and on return
or resume. At an approval gate the stage returns a `blocked`
handoff and stops; root then asks the user without a deadline and re-dispatches only after an
explicit decision is recorded in a new validated handoff.
Functional skills select and record the appropriate mode for their own agent, tool, and shell
invocations. Safety concerns, uncertain side effects, conflicts, and scope changes still require gates.

## 5. Global Invariants

- Root orchestration owns all phase transitions and gate status.
- A stage may rely only on its workflow, validated handoff, authorized artifacts/tools, and evidence
  it independently retrieves. Missing information is unknown or blocking, never recovered from chat.
- Preserve facts, assumptions, constraints, decisions, rejected approaches, open questions, blockers,
  failures, and artifacts as distinct contract types; never silently promote an assumption.
- No transition occurs until its contract passes structural, evidence, epistemic, and workflow
  validation. Workflow amendments are explicit and versioned.
- Contracts contain evidence-backed outcomes, not chain-of-thought, scratchpads, tool chatter, raw
  exploration, or irrelevant conversation history.
- Never infer user approval. Pause at every gate until an explicit decision is recorded.
- Maximum concurrent Code-Flow-Analyzers: 6.
- Maximum concurrent Feature-Implementers: 3.
- Every investigation-documenter task that changes files has explicit write permission.
- Every Feature-Implementer result has a corresponding Test-Implementer result before validation.
- Root owns the bounded validation attempt counter and all remediation re-dispatch.
- Feature work finishes only on validator `SATISFIED` or a recorded bounded-unresolved state.
- Discover and run available project build, test, lint, and type-check commands before feature
  completion.
- Remove `.tmp/` artifacts after their consuming block finishes. Preserve normal outputs and
  `.dev-dude-run-state.md`.
- Shut down all team agents and delete the team after the final state is recorded.

## 6. Stable Outputs

Architecture documents remain in `./docs/ArchOverview/`. Feature documents remain in
`./docs/<feature-slug>/` and follow
[doc-format-templates.md](references/doc-format-templates.md). Durable state is additive and does not
replace investigation, design, implementation, or verification documents.
