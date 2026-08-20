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

All area task pairs run in parallel (max 4-6 concurrent agents total).
```

Each Code-Flow-Analyzer task should (using the indexer tools from `$INDEXER_CONTEXT`):
1. Use `get_symbols_overview` (or equivalent) on key files in the area
2. Trace major flows from entry points using `find_symbol` and `find_referencing_symbols` (or equivalent)
3. Map internal dependencies and external integration points
4. Document patterns, conventions, and design decisions
5. Create mermaid diagrams for major flows

### Phase 2: Documentation (blocked by Phase 1)

```
Investigation-Documenter tasks:

Capture `git rev-parse HEAD` before writing documents and set that full SHA as `**Source Commit**`
in the overview and every deep-dive.

Task 1: Overview document (blocked by ALL Phase 1 tasks)
  Input: All .tmp/<area>.md and .tmp/ux-<area>.md files
  Output: ./docs/ArchOverview/<project>-architecture-overview.md
  - Executive summary
  - High-level architecture diagram (mermaid)
  - Area summaries with cross-references
  - UX collateral where relevant (simple text-only layout maps)
  - Glossary

Tasks 2-N: Deep-dive documents (each blocked by its own Phase 1 task)
  Input: .tmp/<area>.md and .tmp/ux-<area>.md for the specific area
  Output: ./docs/ArchOverview/<project>-<area-slug>.md
  - Detailed component breakdown
  - Data flow diagrams
  - Key interfaces
  - Dependencies
```

### Vertical Review Gate (blocked by Phase 2; blocks Phase 3)

Present the generated deep-dives to the operator as an editable vertical list. For each vertical,
include its name, brief description, and deep-dive document path. Ask the operator to confirm the
list, exclude named verticals, or add verticals (request a path or brief description when needed).
Wait for explicit confirmation before continuing.

- For exclusions, remove the vertical from the active list and update the overview's summaries,
  cross-references, and diagrams. Keep its generated deep-dive, but do not include it in Phases 3-5.
- For additions, run Phases 1 and 2 for each new vertical and update the overview to include it.
- After any change, present the revised list, including newly generated deep-dives, and request
  confirmation again.

### Phase 3: Verification (blocked by the Vertical Review Gate)

```
Code-Flow-Analyzer tasks (one per document, parallel):
  Input: The overview or an active vertical's generated document
  Process:
    - Verify every file path exists
    - Verify every symbol/class/interface exists
    - Verify code snippets match actual code
    - Verify dependency claims
  Output: ./docs/ArchOverview/.tmp/verification-<doc>.md
```

### Phase 4: Architecture Review (blocked by Phase 3)

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

### Phase 5: Fix Application (blocked by Phase 4)

```
Investigation-Documenter task:
  Input: All verification reports and ./docs/ArchOverview/.tmp/architecture-review.md
  Process:
    - Apply corrections to documents
    - Update inaccurate file paths, symbol names, descriptions
    - Fold in architecture review findings and future considerations
    - Note any items that couldn't be verified
  Output: Updated documents in ./docs/ArchOverview/
  Cleanup: Remove .tmp/ directory
```

## Additive Investigation (Specific Area)

Triggered when a specific area is requested AND `./docs/ArchOverview/` already exists.

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

Run Code-Flow-Analyzer and UX-Design-Reviewer tasks in parallel only for affected existing areas and
confirmed new verticals. Give each task the relevant diff, target commit, existing document context,
and `$INDEXER_CONTEXT`. Existing-area tasks must focus on changed flows and their transitive effects;
new-vertical tasks perform a complete investigation of that vertical.

### Step 3: Update Documents

Run Investigation-Documenter tasks to:
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
Architecture-Reviewer on the refreshed scope and Investigation-Documenter to apply corrections and
future considerations. Ensure each refresh row summarizes the finalized changes. Remove
`./docs/ArchOverview/.tmp/` after fixes are applied.

## Team Lifecycle

- Create team at start of Phase 1
- Assign tasks with proper `blockedBy` dependencies
- Monitor progress via TaskList
- Shut down all agents after Phase 5 completes
- Delete team after shutdown
