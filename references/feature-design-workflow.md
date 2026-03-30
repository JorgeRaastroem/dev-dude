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

Code-Flow-Analyzer task:
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
```

### Step 2: Design Options (blocked by Step 1)

```
Investigation-Documenter task:
  Task: "Create design options for <feature>"
  Input:
    - Feature description/spec
    - Investigation results
    - Architecture docs (if available)
  Process:
    - Analyze investigation findings
    - Generate 2-3 design options
    - For each option: approach, affected modules, complexity, pros/cons
    - Include mermaid diagrams showing how each option integrates
  Output: ./docs/<feature-slug>/design-options.md
```

### USER REVIEW GATE

Present design options to the user:
- Show the design options document content
- Ask user to select an option or provide feedback
- If feedback given, iterate on design options
- Continue only after explicit user approval of a design

## Phase 2: Implementation (after user approval)

### Step 3: Implementation Plan

```
Create implementation plan based on selected design:
  Output: ./docs/<feature-slug>/implementation-plan.md
  Contents:
    - Selected design option summary
    - Ordered list of implementation tasks
    - File-level change plan (new files, modified files)
    - Dependencies between tasks
    - Validation criteria
```

### Step 4: Implementation (tasks may have dependencies)

```
Feature-Implementer tasks (per component/module):
  Each task:
    Input:
      - Relevant section of implementation plan
      - Design document
      - Investigation results for context
    Process:
      - Read existing code patterns using the active code indexer tools
      - Implement the assigned component
      - Run available validation (build, lint)
    Output:
      - Code changes
      - Implementation summary with test specifications
```

Task dependencies follow the implementation plan ordering. Independent components run in parallel; dependent ones are sequenced with `blockedBy`.

### Step 5: Test Implementation (REQUIRED — blocked by corresponding Step 4 tasks)

**You MUST create Test-Implementer tasks. Do NOT skip this step.**

As each Feature-Implementer task from Step 4 completes, it produces an implementation summary
containing test specifications (Phase 4 of the feature-implementer workflow). For each completed
Feature-Implementer task:

1. Extract the test specifications from the Feature-Implementer's output
2. Create a Test-Implementer task using the Task tool:

```
Task tool call:
  subagent_type: "test-implementer"
  description: "Write tests for <component>"
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

3. Set `blockedBy` to the corresponding Feature-Implementer's task ID

Independent test tasks can run in parallel. Wait for ALL Test-Implementer tasks to complete
before proceeding to Step 6.

### Step 6: Validation (blocked by Steps 4 and 5)

```
Step 6a: Run project validation
  - Discover build/test/lint commands from project config
  - Run full validation suite
  - Report results

Step 6b: Code-Flow-Analyzer task
  Task: "Verify implementation matches spec"
  Input:
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
├── design-options.md         # Phase 1 Step 2
├── implementation-plan.md    # Phase 2 Step 3
└── verification.md           # Phase 2 Step 6
```

## Team Lifecycle

- Create team at start of Phase 1
- Pause team between Phase 1 and Phase 2 (user review gate)
- Resume team for Phase 2 after user approval
- Shut down all agents after Phase 2 Step 6 completes
- Delete team after shutdown
