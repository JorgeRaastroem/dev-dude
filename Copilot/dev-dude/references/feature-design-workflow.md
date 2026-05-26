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

### Step 2: Design Options (after Step 1 completes)

Launch an Investigation-Documenter to create design options:

```
agent_type: "investigation-documenter-copilot"
mode: "sync"
prompt:
  - Feature description/spec
  - Investigation results from Step 1
  - UX review results from Step 1
  - Architecture docs (if available)
  - $INDEXER_CONTEXT block
  Process:
    - Analyze investigation findings
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
  - $INDEXER_CONTEXT block
  Process:
    - Critique options for reusability, performance, scalability, and operational cost
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

## Phase 2: Implementation (after user approval)

### Step 5: Implementation Plan

Create implementation plan based on selected design:
```
Output: ./docs/<feature-slug>/implementation-plan.md
Contents:
  - Selected design option summary
  - Ordered list of implementation tasks
  - File-level change plan (new files, modified files)
  - Dependencies between tasks
  - Validation criteria
```

### Step 6: Implementation (tasks may have dependencies)

Launch Feature-Implementer agents per component/module:

```
For each component in the implementation plan:
  agent_type: "feature-implementer-copilot"
  mode: "background" (for independent components)
  mode: "sync" (for components with dependencies on prior ones)
  prompt:
    - Relevant section of implementation plan
    - Design document
    - Investigation results for context
    - $INDEXER_CONTEXT block
    Process:
      - Read existing code patterns using the active code indexer tools
      - Implement the assigned component
      - Run available validation (build, lint)
    Output:
      - Code changes
      - Implementation summary with test specifications
        (section heading: "## Test Specifications for Test-Implementer")

Max 3 concurrent Feature-Implementer agents.
```

Independent components run in parallel (background mode); dependent ones run
sequentially (sync mode or wait for background task to complete first).

### Step 7: Test Implementation (REQUIRED — after corresponding Step 6 tasks)

**You MUST create Test-Implementer tasks. Do NOT skip this step.**

As each Feature-Implementer task from Step 6 completes, it produces an implementation
summary containing test specifications. For each completed Feature-Implementer task:

1. Extract the test specifications from the Feature-Implementer's output
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

  ## Instructions
  1. Find existing test patterns near the modified files
  2. Write tests covering all specifications above
  3. Run the tests and report results
```

Independent test tasks can run in parallel. Wait for ALL Test-Implementer tasks to
complete before proceeding to Step 8.

### Step 8: Validation (after Steps 6 and 7 complete)

```
Step 8a: Run project validation
  - Discover build/test/lint commands from project config
  - Run full validation suite via powershell tool
  - Report results

Step 8b: Code-Flow-Analyzer verification
  agent_type: "code-flow-analyzer-copilot"
  mode: "sync"
  prompt:
    - Original feature spec
    - Design document
    - Implementation summaries
    Process:
      - Verify all design requirements are implemented
      - Verify integration points work as designed
      - Check for incomplete implementations
    Output: ./docs/<feature-slug>/verification.md
```

## Output Structure

```
./docs/<feature-slug>/
├── investigation.md          # Phase 1 Step 1
├── ux-review.md              # Phase 1 Step 1
├── design-options.md         # Phase 1 Steps 2-4
├── implementation-plan.md    # Phase 2 Step 5
└── verification.md           # Phase 2 Step 8
```
