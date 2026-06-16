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

```
TeamCreate → "feature-<slug>"

Task A: Code-Flow-Analyzer
  Task: "Investigate existing flows for <feature>"
  Input:
    - Feature description/spec
    - Relevant architecture docs (if available)
    - Keywords and area hints from the feature description
  Process:
    - Search codebase for related components using the active code indexer tools
    - Trace existing flows that the feature will interact with
    - Identify integration points, extension points, patterns
    - Document constraints, conventions, and anti-patterns to avoid
  Output: ./docs/<feature-slug>/investigation.md

Task B: UX-Design-Reviewer
  Task: "Review UX constraints for <feature>"
  Input:
    - Feature description/spec
    - Relevant screenshots, mockups, or image inputs
    - Relevant architecture docs (if available)
  Process:
    - Inspect current user journeys and affected screens
    - Create or confirm project UX principles
    - Produce UX guidance, accessibility notes, and text-only layout maps
  Output: ./docs/<feature-slug>/ux-review.md
```

### Step 2: Design Options (blocked by Step 1)

```
Investigation-Documenter task:
  Task: "Create design options for <feature>"
  Input:
    - Feature description/spec
    - Investigation results
    - UX review results
    - Architecture docs (if available)
  Process:
    - Analyze investigation findings
    - Generate 2-3 design options
    - For each option: approach, affected modules, complexity, pros/cons
    - Include UX guidance and text-only layout maps for UX-impacting changes
    - Include mermaid diagrams showing how each option integrates
  Output: ./docs/<feature-slug>/design-options.md
```

### Step 3: Architecture Critique (blocked by Step 2)

```
Architecture-Reviewer task:
  Task: "Critique design options for <feature>"
  Input:
    - Feature description/spec
    - Design options document
    - Investigation results
  Process:
    - Critique options for reusability, performance, scalability, and operational cost
    - If criteria are missing, interview the user and define them before final scoring
  Output: ./docs/<feature-slug>/.tmp/architecture-review.md
```

### Step 4: Documentation Refinement (blocked by Step 3)

```
Investigation-Documenter task:
  Task: "Refine design options for <feature>"
  Input:
    - Design options document
    - UX review results
    - Architecture review report
  Process:
    - Fold UX guidance into the design document
    - Summarize architecture critique and future considerations
    - Keep design options ready for user review
  Output: ./docs/<feature-slug>/design-options.md
```

### USER REVIEW GATE

Present design options to the user:
- Show the design options document content
- Ask user to select an option or provide feedback
- If feedback given, iterate on design options
- Continue only after explicit user approval of a design

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
| `planned` | Approved design plus implementation plan | `implemented` |
| `implemented` | Feature-Implementer summaries for all ready tasks | `tested` |
| `tested` | Test-Implementer summaries/results for each implementation summary | `validated` |
| `validated` | Project command results plus semantic verification where required | `satisfied` or remediation |
| `satisfied` | Feature-Validator returns `SATISFIED` | complete |

When resuming directly into Phase 2, read existing docs, task outputs, changed files, and command results to determine the current state. Do not assume validation has already run unless `verification.md` contains a current Feature-Validator decision for the latest changed files.

### Step 5: Implementation Plan

Create or refresh the implementation plan based on the selected design:
```
Output: ./docs/<feature-slug>/implementation-plan.md
Contents:
  - Selected design option summary
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
  subagent_type: "feature-implementer"
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
subagent_type: "test-implementer"
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
    - Run the full relevant validation suite with the available shell tool
    - Capture command, exit code, and concise output summary

  Step 8b: Code-Flow-Analyzer semantic verification
    subagent_type: "code-flow-analyzer"
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
    subagent_type: "feature-validator"
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
| Production code gap, incomplete behavior, or spec mismatch | `feature-implementer` |
| Missing, incorrect, or brittle tests | `test-implementer` |
| Unclear flow behavior or insufficient semantic evidence | `code-flow-analyzer`, then `feature-validator` rerun |
| Ambiguous or conflicting requirement | User clarification gate |
| Verification report formatting/document-only issue | Orchestrator or `investigation-documenter` |

Do not skip directly from remediation implementation to validation. Every Feature-Implementer remediation must produce test specifications and every such output must be followed by Test-Implementer before validation reruns.

## Output Structure

```
./docs/<feature-slug>/
├── investigation.md          # Phase 1 Step 1
├── ux-review.md              # Phase 1 Step 1
├── design-options.md         # Phase 1 Steps 2-4
├── implementation-plan.md    # Phase 2 Step 5
└── verification.md           # Phase 2 Step 8
```

## Team Lifecycle

- Create team at start of Phase 1
- Pause team between Phase 1 and Phase 2 (user review gate)
- Resume team for Phase 2 after user approval
- Shut down all agents after Feature-Validator returns `SATISFIED` or the bounded unresolved state is reported
- Delete team after shutdown
