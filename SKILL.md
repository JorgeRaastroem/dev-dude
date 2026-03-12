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
  Prerequisites: Serena MCP server, Team tools (TeamCreate), and the bundled agent crew
  (code-flow-analyzer, investigation-documenter, feature-implementer, test-implementer).
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

Copy agent definitions from this skill's `agents/` directory to `.claude/agents/` so they become
available as `subagent_type` values for the Task tool.

```
Skill path: <skill-path>/agents/
Target: .claude/agents/

Files to install:
  code-flow-analyzer.md    → .claude/agents/code-flow-analyzer.md
  investigation-documenter.md → .claude/agents/investigation-documenter.md
  feature-implementer.md   → .claude/agents/feature-implementer.md
  test-implementer.md      → .claude/agents/test-implementer.md
```

For each file: check if `.claude/agents/<name>.md` already exists (check both project local claude folder and global). If not, copy it. If it exists,
skip (do not overwrite — user may have customized it).

### Verify Serena MCP

Run `mcp__serena__check_onboarding_performed`. If onboarding hasn't been done, run
`mcp__serena__onboarding` and follow its instructions before proceeding.

### Verify Team Tools

Confirm `TeamCreate` tool is available. If not, print:
```
ERROR: Team tools not available. DevDude requires team/swarm capability.
Ensure your Claude Code configuration supports TeamCreate.
```

### Verify Agent Crew

After installing agents, confirm all 4 subagent types are available via the Task tool:
- `code-flow-analyzer`
- `investigation-documenter`
- `feature-implementer`
- `test-implementer`

### Load Project Context

Read Serena project memories for context about the active project:
```
mcp__serena__list_memories()
→ Read any relevant memories (project_overview, style_and_conventions, etc.)
```

If any prerequisite fails, print the error with remediation steps and stop.

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

Use Serena tools to dynamically discover the project structure — never hardcode areas:

1. `mcp__serena__list_dir(".", recursive=false)` — scan project root
2. `mcp__serena__find_file("package.json", ".")` (or equivalent manifest for the project's language)
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

See [references/arch-investigation-workflow.md](references/arch-investigation-workflow.md) for
detailed phase-by-phase workflow including:
- Phase 1: Parallel investigation (one Code-Flow-Analyzer per area)
- Phase 2: Documentation (Investigation-Documenter creates overview + deep-dives)
- Phase 3: Verification (Code-Flow-Analyzer validates docs against code)
- Phase 4: Fix application (Investigation-Documenter applies corrections)

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

See [references/feature-design-workflow.md](references/feature-design-workflow.md) for details.

1. **Investigation**: Code-Flow-Analyzer investigates relevant existing flows
2. **Design Options**: Investigation-Documenter creates 2-3 design options with diagrams

**USER REVIEW GATE**: Present design options to the user. Wait for explicit approval of a
design option before proceeding to Phase 2. If user gives feedback, iterate on design.

### Phase 2: Implementation (after user approval)

See [references/feature-design-workflow.md](references/feature-design-workflow.md) for details.

3. **Implementation Plan**: Create ordered task list with dependencies
4. **Implementation**: Launch Feature-Implementer tasks (per component, respecting dependencies).
   Each Feature-Implementer outputs an **implementation summary with test specifications**.
5. **Testing (REQUIRED)**: After each Feature-Implementer task completes, you MUST launch a
   corresponding Test-Implementer task. Pass it:
   - The implementation summary and test specifications from the completed Feature-Implementer
   - The design document for behavioral expectations
   - The file paths of newly created/modified code
   Create each Test-Implementer task with `blockedBy` set to its corresponding Feature-Implementer task.
   Do NOT skip this step or proceed to validation without running tests.
6. **Validation**: Run project build/test/lint + Code-Flow-Analyzer verifies against spec

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
- Max 4-6 concurrent Code-Flow-Analyzer agents per investigation phase
- Max 3 concurrent Feature-Implementer agents per implementation phase

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
- Shut down all team agents after workflow completes
- Delete team using TeamDelete
- Remove `.tmp/` investigation artifacts from output directories
- Report final status to user
