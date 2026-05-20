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

Launch one Code-Flow-Analyzer agent per discovered area, all in parallel:

```
For each discovered area, launch a task tool call:
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

```
Task 1: Overview document (needs ALL Phase 1 outputs)
  agent_type: "investigation-documenter-copilot"
  mode: "background"
  prompt:
    - Input: All .tmp/<area>.md files
    - Output: ./docs/ArchOverview/<project>-architecture-overview.md
    - Include: Executive summary, high-level architecture diagram (mermaid),
      area summaries with cross-references, glossary

Tasks 2-N: Deep-dive documents (one per area)
  agent_type: "investigation-documenter-copilot"
  mode: "background"
  prompt:
    - Input: .tmp/<area>.md for the specific area
    - Output: ./docs/ArchOverview/<project>-<area-slug>.md
    - Include: Detailed component breakdown, data flow diagrams,
      key interfaces, dependencies
```

**Wait for all Phase 2 tasks** before proceeding.

### Phase 3: Verification (after all Phase 2 tasks complete)

Launch Code-Flow-Analyzer agents to verify each document:

```
One task per generated document, all in parallel:
  agent_type: "code-flow-analyzer-copilot"
  mode: "background"
  prompt:
    - Input: The generated document
    - Process: Verify every file path, symbol/class/interface,
      code snippet, and dependency claim against actual code
    - Output: ./docs/ArchOverview/.tmp/verification-<doc>.md
```

**Wait for all Phase 3 tasks** before proceeding.

### Phase 4: Fix Application (after all Phase 3 tasks complete)

Launch a single Investigation-Documenter to apply corrections:

```
  agent_type: "investigation-documenter-copilot"
  mode: "sync"
  prompt:
    - Input: All verification reports
    - Process: Apply corrections to documents, update inaccurate
      file paths/symbol names/descriptions, note unverifiable items
    - Output: Updated documents in ./docs/ArchOverview/
    - Cleanup: Remove .tmp/ directory
```

## Additive Investigation (Specific Area)

Triggered when a specific area is requested AND `./docs/ArchOverview/` already exists.

```
Step 1: Code-Flow-Analyzer (sync)
  agent_type: "code-flow-analyzer-copilot"
  mode: "sync"
  prompt: "Deep-dive investigate <specific-area>"
  Input: Area path, existing overview doc for context
  Output: ./docs/ArchOverview/.tmp/<area-slug>.md

Step 2: Two Investigation-Documenters (parallel, after Step 1)
  Task A (background): Create new deep-dive document
    Output: ./docs/ArchOverview/<project>-<area-slug>.md
  Task B (background): Update overview document
    - Add new area section
    - Update cross-references
    - Update high-level diagram if needed

  Wait for both tasks to complete.

Step 3: Code-Flow-Analyzer (sync, after Step 2)
  Verify new/updated content only
  Output: ./docs/ArchOverview/.tmp/verification-<area>.md

Step 4: Investigation-Documenter (sync, after Step 3)
  Apply corrections
  Cleanup: Remove .tmp/ directory
```
