# Feature Implementation Workflow

Detailed functional steps for `DudeWriteMyFeature` after a design option is approved. The root
orchestrator owns transitions and checkpoints using the orchestration contract supplied at
invocation; this skill owns clarification, planning, implementation, and paired testing only.

Apply the **Temporary Artifact Lifecycle** from the supplied `orchestration-state.md`. Preserve every
`.tmp/` input while clarification, implementation, paired testing, validation, remediation, or a
user gate may still reference it; this skill must not delete temporary evidence.

## Entry Contract

Enter with an explicitly approved `design-options.md`. Reconcile
`./docs/<feature-slug>/.dev-dude-run-state.md` and resume at the first incomplete step. Do not infer
approval or repeat output-backed work.

## Step 1: Implementation Clarification Gate

If `implementation-interview.md` is missing or predates the approved design:

1. Derive only unresolved, implementation-critical questions from the feature spec,
   `design-options.md`, `ux-review.md`, and `.tmp/architecture-review.md`.
2. Ask one batched set. For each question give its source, why it blocks implementation, and a
   proposed default the user may accept or explicitly waive.
3. Record every answer or waiver in `implementation-interview.md` and in the run-state gate table.
4. If a decision materially changes scope or approach, return control to the root orchestrator,
   transition back to the feature-design workflow, and require renewed design approval.

The gate is complete only when every derived question is answered or explicitly waived. If no
questions remain, record that result. Fold decisions into the implementation plan; downstream
agents do not need the interview transcript.

## Step 2: Implementation Plan

Create or refresh `implementation-plan.md` with the selected design, clarification decisions,
ordered tasks, expected file changes, dependencies, validation criteria, and remediation attempt.
Create stable task IDs in run state for every planned component.

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
the specifications, run relevant tests, and report results. Wait for all paired test tasks.

## Exit Contract

Return control to the root orchestrator only when:

- the plan exists and every implementation task has implementation and paired test evidence;
- relevant targeted checks run during implementation are recorded; and
- changed paths and current implementation/test summaries are checkpointed.

Set the next transition to `dev-dude-validation` and return control. This skill must not make the
final `SATISFIED` decision or own the bounded validation loop.
