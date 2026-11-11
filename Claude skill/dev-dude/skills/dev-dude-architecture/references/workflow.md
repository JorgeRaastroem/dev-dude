# Architecture Investigation Workflow

Nonnormative examples only. The normative workflow is `workflow.yaml` (root copy
`skills/dev-dude-architecture/references/workflow.yaml`, manifest load set `stage.dev-dude-architecture`). Examples show call shapes;
where they differ from YAML rules (for example model selection, concurrency, or write ownership),
the YAML rules win.

## Example: Phase 1: Parallel Investigation

```
TeamCreate → "arch-investigation"

For each discovered area, create two parallel tasks:
  Task A: "Investigate <area-name>"
    Agent: Code-Flow-Analyzer
    Input:
      - Area path (e.g., "packages/core/auth/")
      - Area description from discovery
      - Key entry points identified
    Output:
      - ./docs/ArchOverview/.tmp/<area-slug>.md

  Task B: "Review UX for <area-name>"
    Agent: UX-Design-Reviewer
    Input:
      - Area path or user-facing scope
      - Existing screens/specs relevant to the area
      - Any project UX guidelines (or instruction to interview user and create them)
    Output:
      - ./docs/ArchOverview/.tmp/ux-<area-slug>.md

Area task pairs run in parallel, at most 6 concurrent agents in total (CNF-CONC-001); batch the rest.
```

## Example: Phase 2: Documentation (blocked by Phase 1)

```
Investigation-Documenter tasks:

Every `investigation-documenter` task must be launched with write permissions.

Capture `git rev-parse HEAD` before writing documents and set that full SHA as `**Source Commit**`
in the overview and every deep-dive.

Task 1: Overview document (blocked by ALL Phase 1 tasks)
  Permissions: write
  Input: All .tmp/<area>.md and .tmp/ux-<area>.md files
  Output: ./docs/ArchOverview/<project>-architecture-overview.md
  - Executive summary
  - High-level architecture diagram (mermaid)
  - Area summaries with cross-references
  - UX collateral where relevant (simple text-only layout maps)
  - Glossary

Tasks 2-N: Deep-dive documents (each blocked by its own Phase 1 task)
  Permissions: write
  Input: .tmp/<area>.md and .tmp/ux-<area>.md for the specific area
  Output: ./docs/ArchOverview/<project>-<area-slug>.md
  - Detailed component breakdown
  - Data flow diagrams
  - Key interfaces
  - Dependencies
```

## Example: Phase 3: Verification (blocked by the Vertical Review Gate)

```
Code-Flow-Analyzer tasks (one per document, parallel, at most 6 concurrent per ARCH-P3-001.R05):
  Input: The overview or an active vertical's generated document
  Process:
    - Verify every file path exists
    - Verify every symbol/class/interface exists
    - Verify code snippets match actual code
    - Verify dependency claims
  Output: ./docs/ArchOverview/.tmp/verification-<doc>.md
```

## Example: Phase 4: Architecture Review (blocked by Phase 3)

```
Architecture-Reviewer task:
  Input:
    - Final architecture overview + active vertical deep-dive documents
    - All verification reports
  Process:
    - Critique the mapped architecture for reusability, performance, scalability, and operational cost
    - If criteria are missing, interview the user and create a lightweight review rubric
    - Create a "Future Considerations" list for the project
  Output: ./docs/ArchOverview/.tmp/architecture-review.md
```

## Example: Phase 5: Fix Application (blocked by Phase 4)

```
Investigation-Documenter task:
  Permissions: write
  Input: All verification reports and ./docs/ArchOverview/.tmp/architecture-review.md
  Process:
    - Apply corrections to documents
    - Update inaccurate file paths, symbol names, descriptions
    - Fold in architecture review findings and future considerations
    - Note any items that couldn't be verified
  Output: Updated documents in ./docs/ArchOverview/
  Cleanup: Remove .tmp/ directory
```

## Example: Additive Investigation (Specific Area)

```
Step 1: Parallel investigation
  Task A: Code-Flow-Analyzer
    Task: "Deep-dive investigate <specific-area>"
    Input: Area path, existing overview doc for context
    Output: ./docs/ArchOverview/.tmp/<area-slug>.md

  Task B: UX-Design-Reviewer
    Task: "Review UX for <specific-area>"
    Input: Area path, relevant screens/specs, existing overview doc for context
    Output: ./docs/ArchOverview/.tmp/ux-<area-slug>.md

Step 2: Investigation-Documenters (2 tasks, blocked by Step 1)
  Permissions: write (both tasks)
  Task A: Create new deep-dive document
    Output: ./docs/ArchOverview/<project>-<area-slug>.md
  Task B: Update overview document
    - Add new area section
    - Update cross-references
    - Update high-level diagram if needed
    - Add UX notes/layout maps if relevant

Step 3: Code-Flow-Analyzer (blocked by Step 2)
  Task: Verify new/updated content only
  Output: ./docs/ArchOverview/.tmp/verification-<area>.md

Step 4: Architecture-Reviewer (blocked by Step 3)
  Task: Critique the new/updated area and produce future considerations
  Output: ./docs/ArchOverview/.tmp/architecture-review.md

Step 5: Investigation-Documenter (blocked by Step 4)
  Task: Apply corrections and fold in architecture review
  Cleanup: Remove .tmp/ directory
```
