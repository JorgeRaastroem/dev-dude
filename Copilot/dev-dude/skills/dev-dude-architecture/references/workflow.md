# Architecture Investigation Workflow

Nonnormative examples only. The normative workflow is `workflow.yaml` (root copy
`skills/dev-dude-architecture/references/workflow.yaml`, manifest load set `stage.dev-dude-architecture`). Examples show call shapes;
where they differ from YAML rules (for example model selection, concurrency, or write ownership),
the YAML rules win.

## Example: Phase 1: Parallel Investigation

```
For each discovered area, launch two task tool calls:
  Task A:
    agent_type: "code-flow-analyzer-copilot"
    mode: "background"
    prompt: "Investigate <area-name>"
    Include in prompt:
      - Area path (e.g., "packages/core/auth/")
      - Area description from discovery
      - Key entry points identified
      - $INDEXER_CONTEXT block
    Expected output:
      - ./docs/ArchOverview/.tmp/<area-slug>.md

  Task B:
    agent_type: "ux-design-reviewer-copilot"
    mode: "background"
    prompt: "Review UX for <area-name>"
    Include in prompt:
      - Area path or user-facing scope
      - Existing screens/specs relevant to the area
      - Any project UX guidelines (or instruction to interview user and create them)
      - $INDEXER_CONTEXT block
    Expected output:
      - ./docs/ArchOverview/.tmp/ux-<area-slug>.md

At most 6 concurrent agents in total (CNF-CONC-001). If more areas, batch them.
```

## Example: Phase 2: Documentation (after all Phase 1 tasks complete)

```
Task 1: Overview document (needs ALL Phase 1 outputs)
  agent_type: "investigation-documenter-copilot"
  permissions: "write"
  mode: "background"
  prompt:
    - Input: All .tmp/<area>.md and .tmp/ux-<area>.md files
    - Output: ./docs/ArchOverview/<project>-architecture-overview.md
    - Include: Executive summary, high-level architecture diagram (mermaid),
      area summaries with cross-references, glossary, and text-only UX collateral when relevant

Tasks 2-N: Deep-dive documents (one per area)
  agent_type: "investigation-documenter-copilot"
  permissions: "write"
  mode: "background"
  prompt:
    - Input: .tmp/<area>.md and .tmp/ux-<area>.md for the specific area
    - Output: ./docs/ArchOverview/<project>-<area-slug>.md
    - Include: Detailed component breakdown, data flow diagrams,
      key interfaces, dependencies, and text-only layout maps when relevant
```

## Example: Phase 3: Verification (after the Vertical Review Gate)

```
One task for the overview and one per active vertical document, in parallel, at most 6 concurrent (ARCH-P3-001.R05):
  agent_type: "code-flow-analyzer-copilot"
  mode: "background"
  prompt:
    - Input: The overview or an active vertical's generated document
    - Process: Verify every file path, symbol/class/interface,
      code snippet, and dependency claim against actual code
    - Output: ./docs/ArchOverview/.tmp/verification-<doc>.md
```

## Example: Phase 4: Critical Architecture Review (after all Phase 3 tasks complete)

```
  agent_type: "architecture-reviewer-copilot"
  mode: "background"
  prompt:
    - Input: Final architecture overview + active vertical deep-dive documents
    - Include: All verification reports
    - Process: Critique reusability, performance, scalability, and operational cost
    - Output: ./docs/ArchOverview/.tmp/architecture-review.md
    - Require: "Future Considerations" list for the project
```

## Example: Phase 5: Fix Application (after Phase 4 completes)

```
  agent_type: "investigation-documenter-copilot"
  permissions: "write"
  mode: "background"
  prompt:
    - Input: All verification reports and ./docs/ArchOverview/.tmp/architecture-review.md
    - Process: Apply corrections to documents, update inaccurate
      file paths/symbol names/descriptions, fold in architecture critique,
      add future considerations, note unverifiable items
    - Output: Updated documents in ./docs/ArchOverview/
    - Cleanup: Remove .tmp/ directory
```

## Example: Additive Investigation (Specific Area)

```
Step 1: Parallel investigation
  Task A:
    agent_type: "code-flow-analyzer-copilot"
    mode: "background"
    prompt: "Deep-dive investigate <specific-area>"
    Input: Area path, existing overview doc for context
    Output: ./docs/ArchOverview/.tmp/<area-slug>.md

  Task B:
    agent_type: "ux-design-reviewer-copilot"
    mode: "background"
    prompt: "Review UX for <specific-area>"
    Input: Area path, relevant screens/specs, existing overview doc for context
    Output: ./docs/ArchOverview/.tmp/ux-<area-slug>.md

Step 2: Two Investigation-Documenters (parallel, after Step 1)
  Permissions: write (both tasks)
  Task A (background): Create new deep-dive document
    Output: ./docs/ArchOverview/<project>-<area-slug>.md
  Task B (background): Update overview document
    - Add new area section
    - Update cross-references
    - Update high-level diagram if needed
    - Add UX notes/layout maps if relevant

  Wait for both tasks with bounded watchdog checks.

Step 3: Code-Flow-Analyzer (background, after Step 2; poll with bounded watchdog checks)
  Verify new/updated content only
  Output: ./docs/ArchOverview/.tmp/verification-<area>.md

Step 4: Architecture-Reviewer (background, after Step 3; poll with bounded watchdog checks)
  Critique the new/updated area and produce future considerations
  Output: ./docs/ArchOverview/.tmp/architecture-review.md

Step 5: Investigation-Documenter (background, after Step 4; poll with bounded watchdog checks)
  Apply corrections and fold in architecture review
  Cleanup: Remove .tmp/ directory
```
