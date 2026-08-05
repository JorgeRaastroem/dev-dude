# Feature Design & Implementation Workflow

Detailed steps for the `DudeWriteMyFeature` command.

## Phase 0: Context Gathering

Before starting the feature workflow:

1. **Check for architecture docs**: Look for `./docs/ArchOverview/`
   - If missing, suggest running `DudeWhereIsMyArch` first (warn but don't block)
   - If present, identify relevant area docs to load
2. **Parse feature input**:
   - Plain text description → use directly
   - File path to spec/PRD → read the file
   - Image paths → read images for visual spec
3. **Read project context** using the active indexer's memory/context tools (e.g., Serena project memories)
4. **Derive feature slug** from the description (lowercase, hyphenated, e.g., "user-profile-caching")

## Phase 1: Design

### Step 1: Investigation

Launch a Code-Flow-Analyzer and UX-Design-Reviewer to investigate the feature:

```
Task A:
  agent_type: "code-flow-analyzer-copilot"
  mode: "sync"
  prompt:
    - Feature description/spec
    - Relevant architecture docs (if available)
    - Keywords and area hints from the feature description
    - $INDEXER_CONTEXT block
    Process:
      - Search codebase for related components using the active code indexer tools
      - Trace existing flows that the feature will interact with
      - Identify integration points, extension points, patterns
      - Document constraints, conventions, and anti-patterns to avoid
    Output: ./docs/<feature-slug>/investigation.md

Task B:
  agent_type: "ux-design-reviewer-copilot"
  mode: "sync"
  prompt:
    - Feature description/spec
    - Relevant screenshots, mockups, or image inputs
    - Relevant architecture docs (if available)
    - $INDEXER_CONTEXT block
    Process:
      - Inspect current user journeys and affected screens
      - Create or confirm project UX principles
      - Produce UX guidance, accessibility notes, and text-only layout maps
    Output: ./docs/<feature-slug>/ux-review.md
```

### Step 1.5: Resource Investigation (after Step 1 completes)

Launch a Technical-Resource-Investigator in `discovery` mode to identify resources that should
inform design — reusable internal components plus authoritative external packages/services/APIs.
This step **consumes `investigation.md`** and does **not** re-trace internal flows.

```
agent_type: "technical-resource-investigator-copilot"
mode: "sync"
model: <fast discovery default from the agent frontmatter>
prompt:
  - Feature description/spec
  - Investigation results from Step 1 (./docs/<feature-slug>/investigation.md)
  - UX review results from Step 1 (when resource choice is UX-affected)
  - Architecture docs (if available)
  - $INDEXER_CONTEXT block
  - $RESOURCE_RESEARCH_CONTEXT block
  Process:
    - Validate reuse candidates surfaced by investigation.md (do not re-trace flows)
    - Identify external candidates ONLY from authoritative/allowlisted sources
    - Separate facts from recommendations; cite every external fact with an allowlisted URL or
      MCP document reference
    - Prefer in-repo reuse unless an external resource is clearly justified
    - Record unavailable sources / research gaps explicitly
  Guardrail: Use only sources permitted by references/trusted-source-policy.md. Every external
  recommendation must carry an allowlisted citation (citation-host invariant). Unverified
  candidates cannot be recommended. Read-only: never fetch/execute third-party code or change
  dependencies.
  Output: ./docs/<feature-slug>/resources-investigation.md
```

### Step 1.6: Resource Critique (conditional, after Step 1.5 completes)

Run a **second** Technical-Resource-Investigator pass in `critique-and-amend` mode using a
**different/stronger model override** to pressure-test the draft. This step is **conditional**: run
it only when external candidates exist **or** the resource choice is material to the architecture. If
neither holds, skip it and record the reason directly in `resources-investigation.md`.

```
agent_type: "technical-resource-investigator-copilot"
mode: "sync"
model: <stronger model override, e.g. a stronger model than the discovery default>
prompt:
  - Feature description/spec
  - Draft ./docs/<feature-slug>/resources-investigation.md from Step 1.5
  - $INDEXER_CONTEXT block
  - $RESOURCE_RESEARCH_CONTEXT block
  Process:
    - Critique candidates for security, reliability, maintenance, license, ecosystem health,
      supply-chain risk, operational cost, citation quality, and uncertainty
    - Demote any candidate that fails the citation-host invariant to `unverified`
  Guardrail: Use only sources permitted by references/trusted-source-policy.md. APPEND critique and
  amendments — do NOT delete or overwrite first-pass evidence or citations. Prefer read-only
  advisory sources (GitHub Security Advisories, OSV); do not rely on npm audit.
  Output (append-only): ./docs/<feature-slug>/resources-investigation.md
          (Critique & Amendments + Revised Recommendations sections)
```

### Step 2: Design Options (after Step 1 completes)

Launch an Investigation-Documenter to create design options:

```
agent_type: "investigation-documenter-copilot"
mode: "sync"
prompt:
  - Feature description/spec
  - Investigation results from Step 1
  - Resource investigation results from Steps 1.5/1.6 (./docs/<feature-slug>/resources-investigation.md)
  - UX review results from Step 1
  - Architecture docs (if available)
  - $INDEXER_CONTEXT block
  Process:
    - Analyze investigation findings
    - Incorporate recommended/validated resources from resources-investigation.md as
      architecture-facing inputs (not implementation tasks)
    - Generate 2-3 design options
    - For each option: approach, affected modules, complexity, pros/cons
    - Include UX guidance and text-only layout maps for UX-impacting changes
    - Include mermaid diagrams showing how each option integrates
  Output: ./docs/<feature-slug>/design-options.md
```

### Step 3: Architecture Critique (after Step 2 completes)

Launch an Architecture-Reviewer to critique the design options:

```
agent_type: "architecture-reviewer-copilot"
mode: "sync"
prompt:
  - Feature description/spec
  - Design options document
  - Investigation results
  - Resource investigation results (./docs/<feature-slug>/resources-investigation.md)
  - $INDEXER_CONTEXT block
  Process:
    - Critique options for reusability, performance, scalability, and operational cost
    - Factor in resource recommendations, advisories, license, and supply-chain risk from
      resources-investigation.md
    - If criteria are missing, interview the user and define them before scoring
  Output: ./docs/<feature-slug>/.tmp/architecture-review.md
```

### Step 4: Documentation Refinement (after Step 3 completes)

Launch an Investigation-Documenter to refine the design package:

```
agent_type: "investigation-documenter-copilot"
mode: "sync"
prompt:
  - Design options document
  - UX review results
  - Architecture review report
  - $INDEXER_CONTEXT block
  Process:
    - Fold UX guidance into the design document
    - Summarize architecture critique and future considerations
    - Keep the design options ready for user review
  Output: ./docs/<feature-slug>/design-options.md
```

### USER REVIEW GATE

Present design options to the user:
- Show the design options document content
- Ask user to select an option or provide feedback
- If feedback given, iterate on design options
- Continue only after explicit user approval of a design

## Implementation Clarification Gate (Phase 2 Entry Precondition)

This gate runs after a design is approved and before Phase 2 implementation planning begins. It is a Phase 2 **entry precondition**, not an end-of-Phase-2 completion check, and it must be reachable on both paths into Phase 2:

- **Fresh path**: immediately after the USER REVIEW GATE approves a design option.
- **Direct Phase 2 resume**: before Step 5, check whether a completed clarification gate already exists for the latest approved design. If `./docs/<feature-slug>/implementation-interview.md` is missing or predates the latest approved design, run the gate now; otherwise treat the gate as satisfied and continue.

Avoid unconditional interrogation. The gate only surfaces questions that are genuinely unresolved and implementation-critical — do not re-ask anything already settled by the approved design.

### Step 4.5: Derive and resolve clarifications

1. **Derive unresolved, implementation-critical questions** from existing artifacts (do not invent questions that the design already answers):
   - `./docs/<feature-slug>/design-options.md` — open questions, recommendation caveats, and the "Architecture Review Notes" / future considerations section
   - `./docs/<feature-slug>/ux-review.md` — unresolved UX decisions and accessibility tradeoffs
   - `./docs/<feature-slug>/.tmp/architecture-review.md` — future considerations, open questions, and flagged risks
   - The feature spec itself — ambiguous or missing requirements
   If no implementation-critical questions remain unresolved, record that the gate completed with no open questions and proceed to Step 5.

2. **Ask the questions as a single batched set**, each with a proposed default, so the user can answer, adjust, or explicitly waive in one pass. For each question include: the source artifact, why it is implementation-critical, and the proposed default the workflow will use if the question is waived.

3. **Record answers or waivers** in `./docs/<feature-slug>/implementation-interview.md` as transcript/decision evidence. Each entry captures the question, the source artifact, the proposed default, and the resolved decision (answered value or explicit waiver accepting the default).

4. **Re-approval check**: if any answer materially changes the scope or approach of the approved design, return to the USER REVIEW GATE to update `design-options.md` and obtain fresh approval before continuing. Minor clarifications that do not change scope or approach proceed directly to Step 5.

The gate is complete when `implementation-interview.md` exists and every derived implementation-critical question has an answer or an explicit waiver. Its decisions are folded into `implementation-plan.md` in Step 5, which remains the single source of truth for downstream agents — they rely on the plan and do not separately consume the interview transcript.

## Phase 2: Implementation (after user approval or direct Phase 2 resume)

Phase 2 is a resumable state machine. Whether the flow arrives from the Phase 1 user review gate or starts directly from an existing approved design/implementation plan, it must reconstruct the current feature state and finish through the validation gate.

### Phase 2 Completion Contract

Phase 2 is not complete until all of these are true:

1. `./docs/<feature-slug>/implementation-plan.md` exists and lists implementation tasks, dependencies, changed-file expectations, and validation criteria.
2. Every implementation task has a completed Feature-Implementer result.
3. Every Feature-Implementer result has a corresponding Test-Implementer result.
4. Project validation commands have been discovered and run, or unavailable commands are explicitly recorded.
5. Semantic verification has run when the feature affects non-trivial flows or integration behavior.
6. `./docs/<feature-slug>/verification.md` exists and records the final Feature-Validator decision.
7. The final Feature-Validator status is `SATISFIED`, unless the bounded remediation limit has been reached and unresolved findings are reported.

### Phase 2 State Model

Track the feature through these states:

| State | Required evidence | Next state |
|-------|-------------------|------------|
| `planned` | Approved design, completed clarification gate (`implementation-interview.md`), and implementation plan | `implemented` |
| `implemented` | Feature-Implementer summaries for all ready tasks | `tested` |
| `tested` | Test-Implementer summaries/results for each implementation summary | `validated` |
| `validated` | Project command results plus semantic verification where required | `satisfied` or remediation |
| `satisfied` | Feature-Validator returns `SATISFIED` | complete |

When resuming directly into Phase 2, read existing docs, task outputs, changed files, and command results to determine the current state. First confirm the Implementation Clarification Gate has been completed for the latest approved design (see the gate's direct-resume check); run it before Step 5 if `implementation-interview.md` is missing or predates the latest approved design. Do not assume validation has already run unless `verification.md` contains a current Feature-Validator decision for the latest changed files.

### Step 5: Implementation Plan

Create or refresh the implementation plan based on the selected design. Fold the resolved decisions and waivers from `implementation-interview.md` into this plan so it remains the single source of truth for downstream agents:
```
Output: ./docs/<feature-slug>/implementation-plan.md
Contents:
  - Selected design option summary
  - Clarification decisions and waivers folded in from implementation-interview.md
  - Ordered list of implementation tasks
  - File-level change plan (new files, modified files)
  - Dependencies between tasks
  - Validation criteria
  - Phase 2 state record, including current remediation attempt number
```

### Step 6: Implementation (tasks may have dependencies)

Launch Feature-Implementer agents per component/module:

```
For each ready component in the implementation plan:
  agent_type: "feature-implementer-copilot"
  mode: "background" (for independent components)
  mode: "sync" (for components with dependencies on prior ones)
  prompt:
    - Relevant section of implementation plan
    - Design document
    - Investigation results for context
    - Current validation/remediation findings, if this is a remediation iteration
    - $INDEXER_CONTEXT block
    Process:
      - Read existing code patterns using the active code indexer tools
      - Implement only the assigned component or remediation task
      - Run available validation (build, lint)
    Output:
      - Code changes
      - Implementation summary with test specifications
        (section heading: "## Test Specifications for Test-Implementer")

Max 3 concurrent Feature-Implementer agents.
```

Independent components run in parallel (background mode); dependent ones run sequentially (sync mode or wait for background task to complete first).

### Step 7: Test Implementation (REQUIRED after corresponding Step 6 tasks)

**You MUST create Test-Implementer tasks. Do NOT skip this step.**

As each Feature-Implementer task from Step 6 completes, it produces an implementation summary containing test specifications. For each completed Feature-Implementer task:

1. Extract the test specifications from the Feature-Implementer's output.
2. Launch a Test-Implementer task:

```
agent_type: "test-implementer-copilot"
mode: "background"
prompt: |
  You are implementing tests for the <component> of the <feature> feature.

  ## Implementation Summary & Test Specifications
  <paste the implementation summary from the Feature-Implementer output>

  ## Design Context
  Read the design document at: ./docs/<feature-slug>/design-options.md

  ## Files to Test
  <list the file paths created/modified by the Feature-Implementer>

  ## Validation or Remediation Context
  <include failed criteria from the latest verification report when this is a remediation iteration>

  ## Instructions
  1. Find existing test patterns near the modified files
  2. Write tests covering all specifications above
  3. Run the relevant tests and report results
```

Independent test tasks can run in parallel. Wait for ALL Test-Implementer tasks to complete before proceeding to Step 8.

### Step 8: Validation Loop (REQUIRED after Steps 6 and 7)

Run the validation loop after every implementation/test batch. The default remediation limit is 3 validation attempts unless the user explicitly sets a different limit.

```
while remediation_attempt <= max_remediation_attempts:
  Step 8a: Run project validation
    - Discover build/test/lint/type-check commands from project config
    - Run the full relevant validation suite via powershell tool
    - Capture command, exit code, and concise output summary

  Step 8b: Code-Flow-Analyzer semantic verification
    agent_type: "code-flow-analyzer-copilot"
    mode: "sync"
    prompt:
      - Original feature spec
      - Approved design document
      - Implementation plan
      - Implementation summaries
      - Test summaries/results
      - Changed files
      - $INDEXER_CONTEXT block
      Process:
        - Verify all design requirements are implemented
        - Verify integration points work as designed
        - Check for incomplete implementations
        - Report evidence and uncertainty, not a final gate decision

  Step 8c: Feature-Validator final gate
    agent_type: "feature-validator-copilot"
    mode: "sync"
    prompt:
      - Original feature spec
      - Approved design document
      - Implementation plan and Phase 2 state
      - Implementation summaries
      - Test summaries/results
      - Changed files
      - Project validation command results
      - Code-Flow-Analyzer findings
      - Current remediation attempt number and max attempts
      - $INDEXER_CONTEXT block
    Output: ./docs/<feature-slug>/verification.md

  if Feature-Validator returns SATISFIED:
    complete Phase 2
  else:
    classify each failed criterion by owner agent
    launch targeted remediation tasks
    repeat Step 6 -> Step 7 -> Step 8
```

### Remediation Routing

| Failed criterion | Owner |
|------------------|-------|
| Production code gap, incomplete behavior, or spec mismatch | `feature-implementer-copilot` |
| Missing, incorrect, or brittle tests | `test-implementer-copilot` |
| Unclear flow behavior or insufficient semantic evidence | `code-flow-analyzer-copilot`, then `feature-validator-copilot` rerun |
| Ambiguous or conflicting requirement | User clarification gate |
| Verification report formatting/document-only issue | Orchestrator or `investigation-documenter-copilot` |

Do not skip directly from remediation implementation to validation. Every Feature-Implementer remediation must produce test specifications and every such output must be followed by Test-Implementer before validation reruns.

## Output Structure

```
./docs/<feature-slug>/
├── investigation.md          # Phase 1 Step 1
├── ux-review.md              # Phase 1 Step 1
├── resources-investigation.md # Phase 1 Steps 1.5-1.6
├── design-options.md         # Phase 1 Steps 2-4
├── implementation-interview.md  # Implementation Clarification Gate (Step 4.5)
├── implementation-plan.md    # Phase 2 Step 5
└── verification.md           # Phase 2 Step 8
```
