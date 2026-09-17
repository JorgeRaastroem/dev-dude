# Feature Design Workflow

Detailed functional steps for `DudeWriteMyFeature` from input gathering through explicit design
approval. The root orchestrator owns transitions and checkpoints per
[orchestration-state.md](orchestration-state.md); this block does not plan or implement code.

## Entry Contract

Reconcile `./docs/<feature-slug>/.dev-dude-run-state.md` and resume at the first incomplete step.
Check `./docs/ArchOverview/` and warn, without blocking, when architecture documents are absent.
Parse text, document, image, or combined inputs; read relevant project context; and derive the
feature slug.

## Step 1: Investigation

Create the feature team. In parallel, launch:

- `code-flow-analyzer` to trace related flows, integration points, constraints, conventions, and
  reuse candidates into `investigation.md`;
- `ux-design-reviewer` to inspect journeys and screens and write UX, accessibility, and text layout
  guidance into `ux-review.md`.

Include relevant architecture documents, `$INDEXER_CONTEXT`, and the orchestration envelope in both
tasks. Checkpoint each result independently.

## Step 2: Resource Investigation

After investigation, launch `technical-resource-investigator` in `discovery` mode with the feature
input, `investigation.md`, relevant UX and architecture context, `$INDEXER_CONTEXT`,
`$RESOURCE_RESEARCH_CONTEXT`, and the orchestration envelope.

It validates internal reuse candidates without retracing flows and considers external resources only
from [trusted-source-policy.md](trusted-source-policy.md). Every external fact and recommendation
requires an allowlisted citation; unsupported candidates remain unverified. It is read-only and
writes `resources-investigation.md`.

When external candidates exist or the resource choice is architecturally material, run a second
`critique-and-amend` pass using a stronger model. It critiques security, reliability, maintenance,
licensing, ecosystem health, supply-chain risk, operational cost, citation quality, and uncertainty.
Append amendments without deleting first-pass evidence. Otherwise record why the pass was skipped.

## Step 3: Design Options

Launch `investigation-documenter` with write permission, all prior outputs, relevant architecture
documents, `$INDEXER_CONTEXT`, and the orchestration envelope. Create `design-options.md` with two or
three approaches, affected modules, complexity, trade-offs, diagrams, and UX guidance.

## Step 4: Architecture Critique and Refinement

Launch `architecture-reviewer` with the spec and design evidence. Critique reuse, performance,
scalability, operational cost, resource risk, and unresolved criteria into
`.tmp/architecture-review.md`. Then launch `investigation-documenter` with write permission to fold
the critique and UX guidance into `design-options.md` without hiding open questions.

## User Review Gate

Present the refined options and ask the user to select one or provide feedback. Record
`waiting-for-user` before asking.

- Feedback returns to the relevant design step.
- Only an explicit selection marks the gate approved.
- Record the decision evidence and approved design in run state.

## Exit Contract

Return control to the root orchestrator only when `investigation.md`, `ux-review.md`,
`resources-investigation.md`, and refined `design-options.md` have reconciled evidence and the user
review gate contains an explicit approval.

The next permitted block is
[feature-implementation-workflow.md](feature-implementation-workflow.md). This design block must not
create an implementation plan, modify production code, implement tests, or perform final validation.
