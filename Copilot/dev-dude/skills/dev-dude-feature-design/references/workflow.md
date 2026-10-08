# Feature Design Workflow

Detailed functional steps for `DudeWriteMyFeature` from input gathering through explicit design
approval. The root orchestrator owns transitions and checkpoints using the orchestration contract
supplied at invocation; this skill does not plan or implement code.

All execution examples follow the supplied controlled/cooperative monitoring policy. Background
launches and bounded polls apply when supported; otherwise use the runtime's supported invocation
and record unavailable live monitoring. Neither deadlines nor missing outputs prove work stopped.
Resume or retry only after prior invocations and descendants are confirmed quiescent and reconciled.

## Entry Contract

Reconcile `./docs/<feature-slug>/.dev-dude-run-state.md` and resume at the first incomplete step.
Check `./docs/ArchOverview/` and warn, without blocking, when architecture documents are absent.
Parse text, document, image, or combined inputs; read relevant project context; and derive the
feature slug.

## Step 1: Investigation

Launch as background tasks and poll each with bounded watchdog checks:

- `code-flow-analyzer-copilot` to trace related flows, integration points, constraints, conventions,
  and reuse candidates into `investigation.md`;
- `ux-design-reviewer-copilot` to inspect journeys and screens and write UX, accessibility, and text
  layout guidance into `ux-review.md`.

Pass each agent's frontmatter `model` alias. Include relevant architecture documents,
`$INDEXER_CONTEXT`, and the orchestration envelope in both tasks. Checkpoint each result.

## Step 2: Resource Investigation

After investigation, launch `technical-resource-investigator-copilot` as a background task in `discovery` mode with its
model alias, the feature input, `investigation.md`, relevant UX and architecture context,
`$INDEXER_CONTEXT`, `$RESOURCE_RESEARCH_CONTEXT`, and the orchestration envelope.

It validates internal reuse candidates without retracing flows and considers external resources only
from the trusted-source policy supplied by the root orchestrator. Every external fact and recommendation
requires an allowlisted citation; unsupported candidates remain unverified. It is read-only and
writes `resources-investigation.md`.

When external candidates exist or the resource choice is architecturally material, run a second
background `critique-and-amend` pass using a stronger model. Poll each pass with bounded watchdog
checks before consuming its output. It critiques security, reliability, maintenance,
licensing, ecosystem health, supply-chain risk, operational cost, citation quality, and uncertainty.
Append amendments without deleting first-pass evidence. Otherwise record why the pass was skipped.

## Step 3: Design Options

Launch `investigation-documenter-copilot` in background mode with its model alias and write permission.
Poll with bounded watchdog checks before consuming its output.
Pass all prior outputs, relevant architecture documents, `$INDEXER_CONTEXT`, and the orchestration
envelope. Create `design-options.md` with two or three approaches, affected modules, complexity,
trade-offs, diagrams, and UX guidance.

## Step 4: Architecture Critique and Refinement

Launch `architecture-reviewer-copilot` in background mode with its model alias, spec, and design evidence.
Poll with bounded watchdog checks before consuming its output.
Critique reuse, performance, scalability, operational cost, resource risk, and unresolved criteria
into `.tmp/architecture-review.md`. Then launch `investigation-documenter-copilot` in background mode with
its model alias and write permission; poll with bounded watchdog checks to fold critique and UX guidance into `design-options.md`
without hiding open questions.

## User Review Gate

Return a `blocked` handoff with the refined options and a blocking approval question to root.
Root validates the handoff, records `waiting-for-user`, and presents the options to the user.
Do not keep a stage invocation running while waiting for a decision.

- Feedback returns via a new validated handoff to the relevant design step.
- Only an explicit selection recorded by root marks the gate approved.
- Root records decision evidence and approved design in run state, then re-dispatches this stage.

## Exit Contract

Return control to root at the user gate with a `blocked` handoff. Complete the stage only when
`investigation.md`, `ux-review.md`, `resources-investigation.md`, and refined `design-options.md`
have reconciled evidence and the gate contains an explicit approval.

The next permitted skill is `dev-dude-feature-implementation`. This design skill must not
create an implementation plan, modify production code, implement tests, or perform final validation.
