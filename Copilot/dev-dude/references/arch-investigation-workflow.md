# Architecture Investigation Workflow

Detailed steps for the `DudeWhereIsMyArch` command.

## Phase 0: Codebase Discovery

Before any investigation, dynamically discover the project structure:

1. **Scan project root**: Use the indexer's `list_dir` capability (e.g., `mcp__serena__list_dir(".", recursive=false)`) to see top-level structure
2. **Read indexer memories/context**: Use the indexer's memory/context tools (e.g., `mcp__serena__list_memories()`) then read relevant ones for existing context
3. **Identify package/module boundaries**:
   - Look for `package.json`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `pyproject.toml` etc.
   - Use `find_file` capability (e.g., `mcp__serena__find_file("package.json", ".")`) or equivalent for the project's language
   - Scan key directories: `src/`, `packages/`, `libs/`, `modules/`, `apps/`, `services/`
4. **Identify tech stack**: Read root config files to determine languages, frameworks, build tools
5. **Build area list**: Create a list of investigation areas from discovered modules/packages/directories
6. **Identify entry points**: Look for main files, app entry points, server startup, route definitions

Output: A structured list of areas to investigate with paths and brief descriptions.

## Base Investigation (Full Codebase)

Triggered when area is "all"/broad OR `./docs/ArchOverview/` doesn't exist.

### Phase 1: Parallel Investigation

Launch a Code-Flow-Analyzer and UX-Design-Reviewer agent per discovered area, all in parallel:

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

Max 4-6 concurrent agents. If more areas, batch them.
```

Each Code-Flow-Analyzer task should (using the indexer tools from `$INDEXER_CONTEXT`):
1. Use `get_symbols_overview` (or equivalent) on key files in the area
2. Trace major flows from entry points using `find_symbol` and `find_referencing_symbols` (or equivalent)
3. Map internal dependencies and external integration points
4. Document patterns, conventions, and design decisions
5. Create mermaid diagrams for major flows

**Wait for all Phase 1 tasks**: Use `read_agent(wait: true)` for each background agent before proceeding to Phase 2.

### Phase 2: Documentation (after all Phase 1 tasks complete)

Launch Investigation-Documenter agents:

Capture `git rev-parse HEAD` before writing documents and set that full SHA as `**Source Commit**`
in the overview and every deep-dive.

```
Task 1: Overview document (needs ALL Phase 1 outputs)
  agent_type: "investigation-documenter-copilot"
  mode: "background"
  prompt:
    - Input: All .tmp/<area>.md and .tmp/ux-<area>.md files
    - Output: ./docs/ArchOverview/<project>-architecture-overview.md
    - Include: Executive summary, high-level architecture diagram (mermaid),
      area summaries with cross-references, glossary, and text-only UX collateral when relevant

Tasks 2-N: Deep-dive documents (one per area)
  agent_type: "investigation-documenter-copilot"
  mode: "background"
  prompt:
    - Input: .tmp/<area>.md and .tmp/ux-<area>.md for the specific area
    - Output: ./docs/ArchOverview/<project>-<area-slug>.md
    - Include: Detailed component breakdown, data flow diagrams,
      key interfaces, dependencies, and text-only layout maps when relevant
```

**Wait for all Phase 2 tasks** before proceeding.

### Vertical Review Gate (after Phase 2; before Phase 3)

Present the generated deep-dives to the operator as an editable vertical list. For each vertical,
include its name, brief description, and deep-dive document path. Ask the operator to confirm the
list, exclude named verticals, or add verticals (request a path or brief description when needed).
Wait for explicit confirmation before continuing.

- For exclusions, remove the vertical from the active list and update the overview's summaries,
  cross-references, and diagrams. Keep its generated deep-dive, but do not include it in Phases 3-5.
- For additions, run Phases 1 and 2 for each new vertical and update the overview to include it.
- After any change, present the revised list, including newly generated deep-dives, and request
  confirmation again.

### Phase 3: Verification (after the Vertical Review Gate)

Launch Code-Flow-Analyzer agents to verify each document:

```
One task for the overview and one per active vertical document, all in parallel:
  agent_type: "code-flow-analyzer-copilot"
  mode: "background"
  prompt:
    - Input: The overview or an active vertical's generated document
    - Process: Verify every file path, symbol/class/interface,
      code snippet, and dependency claim against actual code
    - Output: ./docs/ArchOverview/.tmp/verification-<doc>.md
```

**Wait for all Phase 3 tasks** before proceeding.

### Phase 4: Critical Architecture Review (after all Phase 3 tasks complete)

Launch a single Architecture-Reviewer to critique the mapped architecture:

```
  agent_type: "architecture-reviewer-copilot"
  mode: "sync"
  prompt:
    - Input: Final architecture overview + active vertical deep-dive documents
    - Include: All verification reports
    - Process: Critique reusability, performance, scalability, and operational cost
    - Output: ./docs/ArchOverview/.tmp/architecture-review.md
    - Require: "Future Considerations" list for the project
```

### Phase 5: Fix Application (after Phase 4 completes)

Launch a single Investigation-Documenter to apply corrections:

```
  agent_type: "investigation-documenter-copilot"
  mode: "sync"
  prompt:
    - Input: All verification reports and ./docs/ArchOverview/.tmp/architecture-review.md
    - Process: Apply corrections to documents, update inaccurate
      file paths/symbol names/descriptions, fold in architecture critique,
      add future considerations, note unverifiable items
    - Output: Updated documents in ./docs/ArchOverview/
    - Cleanup: Remove .tmp/ directory
```

## Additive Investigation (Specific Area)

Triggered when a specific area is requested AND `./docs/ArchOverview/` already exists.

```
Step 1: Parallel investigation
  Task A:
    agent_type: "code-flow-analyzer-copilot"
    mode: "sync"
    prompt: "Deep-dive investigate <specific-area>"
    Input: Area path, existing overview doc for context
    Output: ./docs/ArchOverview/.tmp/<area-slug>.md

  Task B:
    agent_type: "ux-design-reviewer-copilot"
    mode: "sync"
    prompt: "Review UX for <specific-area>"
    Input: Area path, relevant screens/specs, existing overview doc for context
    Output: ./docs/ArchOverview/.tmp/ux-<area-slug>.md

Step 2: Two Investigation-Documenters (parallel, after Step 1)
  Task A (background): Create new deep-dive document
    Output: ./docs/ArchOverview/<project>-<area-slug>.md
  Task B (background): Update overview document
    - Add new area section
    - Update cross-references
    - Update high-level diagram if needed
    - Add UX notes/layout maps if relevant

  Wait for both tasks to complete.

Step 3: Code-Flow-Analyzer (sync, after Step 2)
  Verify new/updated content only
  Output: ./docs/ArchOverview/.tmp/verification-<area>.md

Step 4: Architecture-Reviewer (sync, after Step 3)
  Critique the new/updated area and produce future considerations
  Output: ./docs/ArchOverview/.tmp/architecture-review.md

Step 5: Investigation-Documenter (sync, after Step 4)
  Apply corrections and fold in architecture review
  Cleanup: Remove .tmp/ directory
```

## Delta Refresh (`<scope> refresh`)

Triggered when the request matches `<all|vertical> refresh` and `./docs/ArchOverview/` exists. `all`
is a repository-wide scope; any other value names one architecture vertical. If the directory does
not exist, explain that there is nothing to refresh and run the Base Investigation for `all`, or an
Additive Investigation for the named vertical.

### Step 1: Resolve the Delta

1. Require a clean worktree checked out on `main` or `master`; do not switch branches or include
   uncommitted changes. Set the target commit to `git rev-parse HEAD`.
2. Select the current architecture documents in scope: every document for `all`, or the named
   vertical's deep-dive plus the overview for a vertical refresh. Read each selected document's
   `**Source Commit**` value. Use it only when it
   is a commit and an ancestor of the target. If it is absent, invalid, or from divergent history,
   use the oldest commit that added the file
   (`git log --diff-filter=A --follow --format=%H -- <document> | tail -1`).
3. If history is shallow, deepen it before resolving creation commits. If a trustworthy baseline
   still cannot be resolved, warn that a safe delta is unavailable and ask before falling back to a
   Base Investigation.
4. Use `git diff --name-status <document-baseline>..<target>` to collect additions, modifications,
   renames, and deletions relevant to each document. Use the earliest resolved baseline for the
   repository-wide new-area check.
5. For `all`, repeat Phase 0 discovery at the target commit. Compare discovered module, package,
   service, and domain boundaries with the areas covered by the overview and deep-dives. Treat a new
   boundary as a candidate vertical even when its files are not under an existing area's path. For a
   named vertical not yet documented, discover that vertical's boundaries and treat it as new.
6. Map changed files to affected documented areas within the requested scope using paths, symbols,
   dependencies, entry points, and cross-area flows. Produce:
   - affected existing documents and the changes that affect each one;
   - candidate new verticals and supporting paths/entry points;
   - changed files that are documentation-neutral, with the reason they need no refresh.

If there are no affected in-scope documents and no in-scope new verticals, report that the requested
architecture documentation is current and stop without rewriting files.

### Step 2: Investigate Affected and New Areas

Run code-flow-analyzer-copilot and ux-design-reviewer-copilot tasks in parallel only for affected
existing areas and confirmed new verticals. Give each task the relevant diff, target commit, existing
document context, and `$INDEXER_CONTEXT`. Existing-area tasks must focus on changed flows and their
transitive effects; new-vertical tasks perform a complete investigation of that vertical.

### Step 3: Update Documents

Run investigation-documenter-copilot tasks to:
- update each affected deep-dive in place without rewriting unaffected sections;
- create one deep-dive for each confirmed new vertical;
- update the overview only where affected summaries, relationships, diagrams, cross-references, or
  the set of verticals changed;
- preserve existing revision-history rows and prepend one refresh-dated row with a concise summary of
  the changes made to each updated document; initialize new documents with an `Initial document.` row;
- set the header `**Date**` to the newest revision-history date and `**Source Commit**` to the full
  target commit SHA in every document changed or created by this run.

Do not regenerate or touch unaffected deep-dives.

### Step 4: Verify, Review, and Apply Fixes

Verify only changed/new documents and changed overview sections against the target commit. Then run
architecture-reviewer-copilot on the refreshed scope and investigation-documenter-copilot to apply
corrections and future considerations. Ensure each refresh row summarizes the finalized changes.
Remove `./docs/ArchOverview/.tmp/` after fixes are applied.
