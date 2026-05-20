---
name: dev-dude
description: >
  Architecture investigation and feature implementation using agent swarms.
  Works on any codebase — dynamically discovers project structure, areas, and conventions.
  Two sub-commands:
  (1) DudeWhereIsMyArch (aliases: arch, where) — Investigate and document codebase architecture
  using parallel agent swarms. Produces structured architecture docs with mermaid diagrams
  in ./docs/ArchOverview/. Use for full codebase investigation or targeted area deep-dives.
  (2) DudeWriteMyFeature (aliases: feature, write) — Design and implement features using agent
  swarms with a user review gate between design and implementation phases. Accepts feature
  descriptions, spec file paths, or image paths. Produces design docs and implementation in
  ./docs/<feature-slug>/.
  Prerequisites: At least one code-indexing MCP server (e.g., Serena) and the bundled agent
  crew (code-flow-analyzer-copilot, investigation-documenter-copilot, feature-implementer-copilot,
  test-implementer-copilot).
---
argument-hint:
  - "DudeWhereIsMyArch all" — Full codebase architecture investigation
  - "DudeWhereIsMyArch authentication" — Deep-dive into authentication area
  - "DudeWhereIsMyArch src/services/" — Investigate specific directory
  - "DudeWriteMyFeature Add user caching" — Implement feature from description
  - "DudeWriteMyFeature ./specs/my-feature.md" — Implement from spec document
  - "DudeWriteMyFeature ./images/feature-spec.png" — Implement from visual spec

# DevDude

Architecture investigation and feature implementation powered by agent swarms.

## 1. Prerequisites

### Install Agents

Copy agent definitions from this skill's `agents/` directory to `~/.copilot/agents/` so they
become available as custom agent types for the Task tool.

```
Skill path: <skill-path>/agents/
Target: ~/.copilot/agents/

Files to install:
  code-flow-analyzer-copilot.md    → ~/.copilot/agents/code-flow-analyzer-copilot.md
  investigation-documenter-copilot.md → ~/.copilot/agents/investigation-documenter-copilot.md
  feature-implementer-copilot.md   → ~/.copilot/agents/feature-implementer-copilot.md
  test-implementer-copilot.md      → ~/.copilot/agents/test-implementer-copilot.md
```

For each file: check if `~/.copilot/agents/<name>.md` already exists. If not, copy it.
If it exists, skip (do not overwrite — user may have customized it).

### Detect & Select Code Indexers

Discover which code-indexing MCP servers are available in the current environment and let the
user choose which ones to use. At least one indexer is recommended but not required.

1. **Auto-detect available indexers** — probe for known MCP tool prefixes:
   | Indexer | Detection probe | Capabilities |
   |---------|----------------|--------------|
   | Serena | Check for Serena MCP tools (list_dir, find_file, etc.) | list_dir, find_file, search_for_pattern, get_symbols_overview, find_symbol, find_referencing_symbols, replace_symbol_body, insert_after_symbol, insert_before_symbol, rename_symbol, memories (write/read/list/delete/edit), activate_project, onboarding |
   | *Add new indexers here by extending this table* | | |

2. **Present detected indexers** to the user:
   ```
   Detected code indexers:
     [1] Serena  ✓ available
     [2] ...

   Select indexers to use (comma-separated, or 'all'): ___
   ```
   If only one indexer is detected, auto-select it and inform the user.
   If no indexers are detected, proceed with standard tools (grep, glob, view) and inform the user.

3. **Run indexer-specific onboarding** for each selected indexer:
   - Serena: check if onboarded; if not, run onboarding
   - Other indexers: follow their specific onboarding steps

4. **Build the indexer context block** — a structured summary to pass to agents:
   ```
   ## Active Code Indexers
   The following code-indexing MCP servers are available for this session.
   Use these tools for code search, symbol lookup, and codebase navigation.

   ### <Indexer Name>
   - **Tool prefix**: <prefix>
   - **Capabilities**: <comma-separated list>
   - **Key tools for code search**: <list of search/symbol tools>
   - **Key tools for code modification**: <list of edit tools>
   - **Memory/context tools**: <list, if any>
   ```
   Store this block as `$INDEXER_CONTEXT` for inclusion in agent task prompts.

   If no indexers are available, set `$INDEXER_CONTEXT` to:
   ```
   ## Code Search Tools
   No MCP code indexers are available. Use the standard tools:
   - grep: Search file contents with regex patterns
   - glob: Find files by name patterns
   - view: Read file contents
   ```

### Verify Agent Crew

Confirm all 4 custom agent types are available via the Task tool:
- `code-flow-analyzer-copilot`
- `investigation-documenter-copilot`
- `feature-implementer-copilot`
- `test-implementer-copilot`

If any are missing, attempt to install them from this skill's `agents/` directory.

### Load Project Context

If a code indexer is available, use it to load project context. For example, with Serena:
```
list_memories()
→ Read any relevant memories (project_overview, style_and_conventions, etc.)
```
Other indexers: use their equivalent context/memory retrieval tools.

If no prerequisite fails critically, print the error with remediation steps and stop.

## 2. Argument Parsing

Parse `$ARGUMENTS` — the first token determines the command:

| Token | Command |
|-------|---------|
| `DudeWhereIsMyArch`, `arch`, `where` | Architecture Investigation |
| `DudeWriteMyFeature`, `feature`, `write` | Feature Design & Implementation |

Remaining tokens after the command = the argument:
- For `arch`: area name or "all" for full investigation
- For `feature`: feature description text, path to a spec file, or path to images

If no recognized command, print usage:
```
DevDude - Architecture Investigation & Feature Implementation

Usage:
  /dev-dude DudeWhereIsMyArch [area|all]
  /dev-dude DudeWriteMyFeature <description|spec-path|image-paths>

Aliases:
  arch, where  → DudeWhereIsMyArch
  feature, write → DudeWriteMyFeature

Examples:
  /dev-dude arch all                    # Full codebase architecture investigation
  /dev-dude arch authentication         # Deep-dive into auth area
  /dev-dude where src/services/         # Investigate a specific directory
  /dev-dude feature Add user caching    # Implement a feature from description
  /dev-dude write ./specs/my-feature.md # Implement from a spec document
```

## 3. DudeWhereIsMyArch

Investigates and documents codebase architecture using parallel agent swarms.

### Codebase Discovery (Phase 0)

Use the selected code indexer(s) or standard tools to dynamically discover the project structure — never hardcode areas:

1. Scan project root using `list_dir` capability or `glob` to see top-level structure
2. Search for manifest files using `find_file` capability or `glob` patterns
3. Scan key directories to identify module/package boundaries
4. Identify tech stack from config files
5. Build investigation area list from what's actually in the codebase
6. Identify entry points (main files, app bootstrap, route definitions)

### Mode Selection

- **Base Investigation**: area argument is "all" or broad, OR `./docs/ArchOverview/` doesn't exist
  - Full codebase investigation across all discovered areas
  - Creates complete documentation set
- **Additive Investigation**: specific area AND `./docs/ArchOverview/` already exists
  - Targeted deep-dive into the specified area
  - Updates existing overview document with new cross-references

### Swarm Execution

**IMPORTANT**: When creating any agent task, always include `$INDEXER_CONTEXT` in the task
prompt so agents know which code indexer tools are available.

Use the `task` tool to launch agents. For parallel execution, use `mode: "background"` and
then `read_agent(wait: true)` for each agent to wait for completion before starting the next
phase. For sequential execution within a phase, use `mode: "sync"`.

See [references/arch-investigation-workflow.md](references/arch-investigation-workflow.md) for
detailed phase-by-phase workflow including:
- Phase 1: Parallel investigation (one code-flow-analyzer-copilot per area, background mode)
- Phase 2: Documentation (investigation-documenter-copilot creates overview + deep-dives)
- Phase 3: Verification (code-flow-analyzer-copilot validates docs against code)
- Phase 4: Fix application (investigation-documenter-copilot applies corrections)

### Output

```
./docs/ArchOverview/
├── <project>-architecture-overview.md    # High-level overview
├── <project>-<area-1>.md                 # Deep-dive per area
├── <project>-<area-2>.md
└── ...
```

## 4. DudeWriteMyFeature

Designs and implements features using agent swarms with a user review gate.

### Prerequisites Check

Check if `./docs/ArchOverview/` exists. If not, print a warning:
```
WARNING: No architecture docs found at ./docs/ArchOverview/.
Consider running '/dev-dude arch all' first for better design context.
Proceeding without architecture context...
```
This is a warning, not a blocker.

### Input Handling

Parse the feature argument:
- **Plain text**: Use directly as feature description
- **File path** (`.md`, `.txt`, `.docx`, `.pdf`): Read file content as feature spec
- **Image paths** (`.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`): Read images as visual spec
- **Multiple paths**: Combine all inputs

Derive a feature slug from the description (lowercase, hyphenated, max 40 chars).

### Phase 1: Design

**IMPORTANT**: Include `$INDEXER_CONTEXT` in all agent task prompts.

See [references/feature-design-workflow.md](references/feature-design-workflow.md) for details.

1. **Investigation**: code-flow-analyzer-copilot investigates relevant existing flows (sync)
2. **Design Options**: investigation-documenter-copilot creates 2-3 design options with diagrams (sync)

**USER REVIEW GATE**: Present design options to the user. Wait for explicit approval of a
design option before proceeding to Phase 2. If user gives feedback, iterate on design.

### Phase 2: Implementation (after user approval)

See [references/feature-design-workflow.md](references/feature-design-workflow.md) for details.

3. **Implementation Plan**: Create ordered task list with dependencies
4. **Implementation**: Launch feature-implementer-copilot tasks (per component, respecting dependencies).
   - Independent components: `mode: "background"` (max 3 concurrent)
   - Dependent components: `mode: "sync"` or wait for background tasks first
   Each feature-implementer-copilot outputs an **implementation summary with test specifications**.
5. **Testing (REQUIRED)**: After each feature-implementer-copilot task completes, you MUST launch a
   corresponding test-implementer-copilot task. Pass it:
   - The implementation summary and test specifications from the completed feature-implementer
   - The design document for behavioral expectations
   - The file paths of newly created/modified code
   Do NOT skip this step or proceed to validation without running tests.
6. **Validation**: Run project build/test/lint + code-flow-analyzer-copilot verifies against spec

### Output

```
./docs/<feature-slug>/
├── investigation.md
├── design-options.md
├── implementation-plan.md
└── verification.md
```

## 5. Output Format

All documents follow templates in [references/doc-format-templates.md](references/doc-format-templates.md).

Key format requirements:
- **Metadata header**: Date, scope, tech stack
- **Table of contents**: For documents with 3+ sections
- **Mermaid diagrams**: For architecture views and data flows
- **File path references**: Every code reference includes relative file path
- **Cross-references**: Links between related documents
- **Glossary**: Domain-specific terms in overview documents

## 6. Guard Rails

### Concurrency Limits
- Max 4-6 concurrent code-flow-analyzer-copilot agents per investigation phase
- Max 3 concurrent feature-implementer-copilot agents per implementation phase

### User Confirmation
- Always pause for user approval between design and implementation phases
- Present design options clearly with pros/cons before asking for selection

### Validation
After implementation, discover and run appropriate project validation:
- Look for build commands in `package.json` scripts, `Makefile`, `Cargo.toml`, etc.
- Look for test commands (test, test:unit, pytest, cargo test, go test, etc.)
- Look for lint commands (lint, eslint, clippy, golint, etc.)
- Run discovered commands and report results

### Cleanup
- Remove `.tmp/` investigation artifacts from output directories
- Report final status to user
