# Architecture Investigation Workflow

Detailed steps for the `DudeWhereIsMyArch` command.

## Phase 0: Codebase Discovery

Before any investigation, dynamically discover the project structure:

1. **Scan project root**: `mcp__serena__list_dir(".", recursive=false)` to see top-level structure
2. **Read Serena memories**: `mcp__serena__list_memories()` then read relevant ones for existing context
3. **Identify package/module boundaries**:
   - Look for `package.json`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `pyproject.toml` etc.
   - Use `mcp__serena__find_file("package.json", ".")` or equivalent for the project's language
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

For each discovered area, create a Code-Flow-Analyzer task:
  Task: "Investigate <area-name>"
  Input:
    - Area path (e.g., "packages/core/auth/")
    - Area description from discovery
    - Key entry points identified
  Output:
    - ./docs/ArchOverview/.tmp/<area-slug>.md

All area tasks run in parallel (max 4-6 concurrent).
```

Each Code-Flow-Analyzer task should:
1. Use `get_symbols_overview` on key files in the area
2. Trace major flows from entry points using `find_symbol` and `find_referencing_symbols`
3. Map internal dependencies and external integration points
4. Document patterns, conventions, and design decisions
5. Create mermaid diagrams for major flows

### Phase 2: Documentation (blocked by Phase 1)

```
Investigation-Documenter tasks:

Task 1: Overview document (blocked by ALL Phase 1 tasks)
  Input: All .tmp/<area>.md files
  Output: ./docs/ArchOverview/<project>-architecture-overview.md
  - Executive summary
  - High-level architecture diagram (mermaid)
  - Area summaries with cross-references
  - Glossary

Tasks 2-N: Deep-dive documents (each blocked by its own Phase 1 task)
  Input: .tmp/<area>.md for the specific area
  Output: ./docs/ArchOverview/<project>-<area-slug>.md
  - Detailed component breakdown
  - Data flow diagrams
  - Key interfaces
  - Dependencies
```

### Phase 3: Verification (blocked by Phase 2)

```
Code-Flow-Analyzer tasks (one per document, parallel):
  Input: The generated document
  Process:
    - Verify every file path exists
    - Verify every symbol/class/interface exists
    - Verify code snippets match actual code
    - Verify dependency claims
  Output: ./docs/ArchOverview/.tmp/verification-<doc>.md
```

### Phase 4: Fix Application (blocked by Phase 3)

```
Investigation-Documenter task:
  Input: All verification reports
  Process:
    - Apply corrections to documents
    - Update inaccurate file paths, symbol names, descriptions
    - Note any items that couldn't be verified
  Output: Updated documents in ./docs/ArchOverview/
  Cleanup: Remove .tmp/ directory
```

## Additive Investigation (Specific Area)

Triggered when a specific area is requested AND `./docs/ArchOverview/` already exists.

```
Step 1: Code-Flow-Analyzer
  Task: "Deep-dive investigate <specific-area>"
  Input: Area path, existing overview doc for context
  Output: ./docs/ArchOverview/.tmp/<area-slug>.md

Step 2: Investigation-Documenters (2 tasks, blocked by Step 1)
  Task A: Create new deep-dive document
    Output: ./docs/ArchOverview/<project>-<area-slug>.md
  Task B: Update overview document
    - Add new area section
    - Update cross-references
    - Update high-level diagram if needed

Step 3: Code-Flow-Analyzer (blocked by Step 2)
  Task: Verify new/updated content only
  Output: ./docs/ArchOverview/.tmp/verification-<area>.md

Step 4: Investigation-Documenter (blocked by Step 3)
  Task: Apply corrections
  Cleanup: Remove .tmp/ directory
```

## Team Lifecycle

- Create team at start of Phase 1
- Assign tasks with proper `blockedBy` dependencies
- Monitor progress via TaskList
- Shut down all agents after Phase 4 completes
- Delete team after shutdown
