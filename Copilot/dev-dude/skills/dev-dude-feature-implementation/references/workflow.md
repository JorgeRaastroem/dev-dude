# Feature Implementation Workflow

Detailed functional steps for `DudeWriteMyFeature` after a design option is approved. The root
orchestrator owns transitions and checkpoints using the orchestration contract supplied at
invocation; this skill owns clarification, planning, implementation, and paired testing only.

All execution examples follow the supplied controlled/cooperative monitoring policy. Background
launches and bounded polls apply when supported; otherwise use the runtime's supported invocation
and record unavailable live monitoring. Neither deadlines nor missing outputs prove work stopped.
Resume or retry only after prior invocations and descendants are confirmed quiescent and reconciled.

## Entry Contract

Enter with an explicitly approved `design-options.md`. Reconcile
`./docs/<feature-slug>/.dev-dude-run-state.md` and resume at the first incomplete step. Do not infer
approval or repeat output-backed work.

## Step 1: Implementation Clarification Gate

If `implementation-interview.md` is missing or predates the approved design:

1. Derive only unresolved, implementation-critical questions from the feature spec,
   `design-options.md`, `ux-review.md`, and `.tmp/architecture-review.md`.
2. Return a `blocked` handoff to root with one batched set. For each question give its source,
   why it blocks implementation, and a proposed default the user may accept or explicitly waive.
   Root records `waiting-for-user`, asks the user, and re-dispatches this stage with the decision in
   a new validated handoff; do not keep a stage invocation running while waiting.
3. Record every answer or waiver in `implementation-interview.md`; root records its decision
   evidence in the run-state gate table.
4. If a decision materially changes scope or approach, return a `blocked` contract to root with
   the decision evidence and why the approved design is no longer valid. Root supersedes this
   implementation attempt and routes to feature design with a new root-produced, validated design
   input contract; the blocked implementation handoff itself does not authorize a cross-stage
   transition. Require renewed design approval before returning to implementation.

The gate is complete only when every derived question is answered or explicitly waived. If no
questions remain, record that result. Fold decisions into the implementation plan; downstream
agents do not need the interview transcript.

## Step 2: Implementation Plan

Create or refresh `implementation-plan.md` with the selected design, clarification decisions,
ordered tasks, expected file changes, dependencies, validation criteria, and remediation attempt.
Record stable task IDs for every planned component in the stage journal; root reconciles them
into run state.

## Step 3: Implementation

For each dependency-ready component, launch `feature-implementer-copilot` with:

- its plan section, approved design, investigation context, and current remediation findings;
- `$INDEXER_CONTEXT`;
- the orchestration envelope supplied at invocation; and
- a requirement to return changed paths plus an implementation summary headed
  `## Test Specifications for Test-Implementer`.

Pass the selected agent's frontmatter `model` alias to every task call. Run independent tasks in
background mode and at most three Feature-Implementers concurrently. Mark a task complete only when
its expected repository changes and result summary exist.

## Step 4: Test Implementation

Every completed Feature-Implementer or Feature-Implementer remediation requires a corresponding
`test-implementer-copilot` task before validation. Pass its frontmatter `model` alias, implementation
summary and test specifications, approved design, changed paths, remediation context,
`$INDEXER_CONTEXT`, and orchestration envelope. Require it to follow nearby test patterns, implement
the specifications, run relevant tests, and report results. Wait for all paired test tasks with
bounded watchdog checks.

## Exit Contract

Return control to root at the clarification gate with a `blocked` handoff. Complete the stage only when:

- the plan exists and every implementation task has implementation and paired test evidence;
- relevant targeted checks run during implementation are recorded; and
- changed paths and current implementation/test summaries are checkpointed.

Set the next transition to `dev-dude-validation` and return control. This skill must not make the
final `SATISFIED` decision or own the bounded validation loop.
