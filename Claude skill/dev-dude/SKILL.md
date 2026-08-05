---
name: dev-dude
description: >
  Architecture investigation and feature implementation using agent swarms.
  Works on any codebase by dynamically discovering project structure, areas, and conventions.
  Commands: DudeWhereIsMyArch (arch/where) performs parallel architecture investigation and writes
  docs to ./docs/ArchOverview/. DudeWriteMyFeature (feature/write) designs and implements features
  with a user review gate, accepting text prompts, spec files, or image inputs and writing outputs
  to ./docs/<feature-slug>/. Requires at least one code-indexing MCP server, Mermaid tooling,
  TeamCreate, and the bundled agent crew.
---
argument-hint:
  - "DudeWhereIsMyArch all" — Full codebase architecture investigation
  - "DudeWhereIsMyArch allrefresh" — Delta refresh on the current main/master branch
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

Bundled agent crew version: `1.0.4` (all agents must always use the same version).

```
Skill path: <skill-path>/agents/
Target: .claude/agents/

Files to install:
  code-flow-analyzer.md    → .claude/agents/code-flow-analyzer.md
  ux-design-reviewer.md    → .claude/agents/ux-design-reviewer.md
  architecture-reviewer.md → .claude/agents/architecture-reviewer.md
  technical-resource-investigator.md → .claude/agents/technical-resource-investigator.md
  investigation-documenter.md → .claude/agents/investigation-documenter.md
  feature-implementer.md   → .claude/agents/feature-implementer.md
  test-implementer.md      → .claude/agents/test-implementer.md
  feature-validator.md     → .claude/agents/feature-validator.md
```

For each file: compare the bundled version with the installed version in
`.claude/agents/<name>.md` frontmatter (`version:`) (check both project-local and global install).

Rules:
- If installed file is missing, copy bundled file.
- If installed file has no `version`, treat it as `0`.
- If installed version is lower than bundled version, overwrite with bundled file (update).
- If installed version is equal or higher, keep installed file (do not overwrite).

Always update all agent files as one atomic set when any installed version is lower so the crew
remains on one shared version.

### Install Mermaid Validation Tooling

Install Mermaid CLI so investigation-documenter can validate Mermaid diagrams with parser and render checks:

```bash
npm install --global @mermaid-js/mermaid-cli
```

If CLI installation is not possible in the environment, ensure a Mermaid parser/library fallback is available and require explicit reporting that CLI validation was unavailable.

### Detect & Select Code Indexers

Discover which code-indexing MCP servers are available in the current environment and let the
user choose which ones to use. At least one indexer is required.

1. **Auto-detect available indexers** — probe for known MCP tool prefixes:
   | Indexer | Detection probe | Capabilities |
   |---------|----------------|--------------|
   | Serena | `mcp__serena__check_onboarding_performed` | list_dir, find_file, search_for_pattern, get_symbols_overview, find_symbol, find_referencing_symbols, replace_symbol_body, insert_after_symbol, insert_before_symbol, rename_symbol, memories (write/read/list/delete/edit), activate_project, onboarding, think_about_* |
   | *Add new indexers here by extending this table* | | |

2. **Present detected indexers** to the user:
   ```
   Detected code indexers:
     [1] Serena  ✓ available
     [2] ...

   Select indexers to use (comma-separated, or 'all'): ___
   ```
   If only one indexer is detected, auto-select it and inform the user.

3. **Run indexer-specific onboarding** for each selected indexer:
   - Serena: call `mcp__serena__check_onboarding_performed`; if not onboarded, run `mcp__serena__onboarding`
   - Other indexers: follow their specific onboarding steps

4. **Build the indexer context block** — a structured summary to pass to agents:
   ```
   ## Active Code Indexers
   The following code-indexing MCP servers are available for this session.
   Use these tools for code search, symbol lookup, and codebase navigation.

   ### <Indexer Name>
   - **Tool prefix**: mcp__<prefix>__
   - **Capabilities**: <comma-separated list>
   - **Key tools for code search**: <list of search/symbol tools>
   - **Key tools for code modification**: <list of edit tools>
   - **Memory/context tools**: <list, if any>
   ```
   Store this block as `$INDEXER_CONTEXT` for inclusion in agent task prompts.

If no indexers are detected, print:
```
ERROR: No code-indexing MCP servers found. DevDude requires at least one
code indexer (e.g., Serena). Install and configure an indexer, then retry.
```

### Detect Research Sources

Discover which **research** tools are available for technical-resource investigation and build a
context block separate from `$INDEXER_CONTEXT`. This drives the resource investigator's ability to
cite authoritative external sources.

1. **Probe for research tools**:
   - **Documentation MCP servers** (e.g., a docs/context MCP server) — preferred for authoritative,
     citable docs.
   - **GitHub / package registry lookup options** — for repository, release, advisory, and registry
     pages (GitHub, npmjs.com, pypi.org, etc.).
   - **WebFetch / WebSearch availability**.

2. **Build the research context block** — store as `$RESOURCE_RESEARCH_CONTEXT`:
   ```
   ## Research Sources
   The following research tools are available for technical-resource investigation.
   All external research is governed by references/trusted-source-policy.md.

   - **Documentation MCP**: <available servers, or "none">
   - **GitHub / registry lookup**: <available options, or "none">
   - **WebFetch / WebSearch**: <available / unavailable>

   NOTE: WebFetch/WebSearch are policy-bound by the trusted-source policy, NOT technically
   domain-restricted. Only allowlisted authoritative sources may be cited.
   ```

3. **Fallback (no reliable research tools)** — if no documentation MCP and no reliable GitHub/registry
   or web lookup is available, set `$RESOURCE_RESEARCH_CONTEXT` to mark external research
   **unavailable**, and the resource investigator uses repository-local discovery and validation only:
   ```
   ## Research Sources
   No documentation MCP or reliable lookup tool is available. External research is UNAVAILABLE.
   The technical-resource-investigator must use repository-local discovery/validation only and
   record external research as unavailable per references/trusted-source-policy.md.
   ```

### Verify Team Tools

Confirm `TeamCreate` tool is available. If not, print:
```
ERROR: Team tools not available. DevDude requires team/swarm capability.
Ensure your Claude Code configuration supports TeamCreate.
```

### Verify Agent Crew

After installing agents, confirm all 8 subagent types are available via the Task tool:
- `code-flow-analyzer`
- `ux-design-reviewer`
- `architecture-reviewer`
- `technical-resource-investigator`
- `investigation-documenter`
- `feature-implementer`
- `test-implementer`
- `feature-validator`

### Load Project Context

Use the active indexer(s) to load project context. For example, with Serena:
```
mcp__serena__list_memories()
→ Read any relevant memories (project_overview, style_and_conventions, etc.)
```
Other indexers: use their equivalent context/memory retrieval tools.

If any prerequisite fails, print the error with remediation steps and stop.

## 2. Argument Parsing

Parse `$ARGUMENTS` — the first token determines the command:

| Token | Command |
|-------|---------|
| `DudeWhereIsMyArch`, `arch`, `where` | Architecture Investigation |
| `DudeWriteMyFeature`, `feature`, `write` | Feature Design & Implementation |

Remaining tokens after the command = the argument:
- For `arch`: area name, "all" for full investigation, or "allrefresh" for a delta refresh
- For `feature`: feature description text, path to a spec file, or path to images

If no recognized command, print usage:
```
DevDude - Architecture Investigation & Feature Implementation

Usage:
  /dev-dude DudeWhereIsMyArch [area|all|allrefresh]
  /dev-dude DudeWriteMyFeature <description|spec-path|image-paths>

Aliases:
  arch, where  → DudeWhereIsMyArch
  feature, write → DudeWriteMyFeature

Examples:
  /dev-dude arch all                    # Full codebase architecture investigation
  /dev-dude arch allrefresh             # Refresh affected docs on main/master
  /dev-dude arch authentication         # Deep-dive into auth area
  /dev-dude where src/services/         # Investigate a specific directory
  /dev-dude feature Add user caching    # Implement a feature from description
  /dev-dude write ./specs/my-feature.md # Implement from a spec document
```

## 3. DudeWhereIsMyArch

Investigates and documents codebase architecture using parallel agent swarms.

### Codebase Discovery (Phase 0)

Use the selected code indexer(s) to dynamically discover the project structure — never hardcode areas:

1. Scan project root using `list_dir` capability (e.g., `mcp__serena__list_dir(".", recursive=false)`)
2. Search for manifest files using `find_file` capability (e.g., `mcp__serena__find_file("package.json", ".")`)
3. Scan key directories to identify module/package boundaries
4. Identify tech stack from config files
5. Build investigation area list from what's actually in the codebase
6. Identify entry points (main files, app bootstrap, route definitions)

### Mode Selection

- **Base Investigation**: area argument is "all" or broad, OR `./docs/ArchOverview/` doesn't exist
  - Full codebase investigation across all discovered areas
  - Creates complete documentation set
- **Delta Refresh**: area argument is "allrefresh" AND `./docs/ArchOverview/` exists
  - Compares each document's source baseline with the current `main` or `master` commit
  - Re-investigates and updates only affected documented areas
  - Discovers and documents new architecture areas introduced by the delta
- **Additive Investigation**: specific area AND `./docs/ArchOverview/` already exists
  - Targeted deep-dive into the specified area
  - Updates existing overview document with new cross-references

### Swarm Execution

**IMPORTANT**: When creating any agent task, always include `$INDEXER_CONTEXT` in the task
prompt so agents know which code indexer tools are available.

See [references/arch-investigation-workflow.md](references/arch-investigation-workflow.md) for
detailed phase-by-phase workflow including:
- Phase 1: Parallel investigation (Code-Flow-Analyzer + UX-Design-Reviewer per area)
- Phase 2: Documentation (Investigation-Documenter creates overview + deep-dives + UX collateral)
- Phase 3: Verification (Code-Flow-Analyzer validates docs against code)
- Phase 4: Critical review (Architecture-Reviewer critiques the mapped architecture)
- Phase 5: Fix application (Investigation-Documenter applies corrections and future considerations)
- Delta refresh: baseline resolution, impact mapping, and scoped document updates for `allrefresh`

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

**IMPORTANT**: Include `$INDEXER_CONTEXT` in all agent task prompts. Additionally, pass both
`$INDEXER_CONTEXT` and `$RESOURCE_RESEARCH_CONTEXT` to the Technical-Resource-Investigator tasks
(Steps 1.5 and 1.6).

See [references/feature-design-workflow.md](references/feature-design-workflow.md) for details.

1. **Investigation**: Code-Flow-Analyzer and UX-Design-Reviewer investigate relevant existing flows and UX constraints
2. **Resource Investigation (Step 1.5)**: Technical-Resource-Investigator (mode `discovery`) consumes `investigation.md`, validates reuse candidates, and identifies authoritative external resources with allowlisted citations → `resources-investigation.md`
3. **Resource Critique (Step 1.6, conditional)**: a second Technical-Resource-Investigator pass (mode `critique-and-amend`, stronger model override) critiques external/material candidates for security, reliability, maintenance, licensing, supply-chain risk, and operational cost, appending amendments without overwriting evidence. Skipped (with reason recorded) when no external or material candidates exist
4. **Design Options**: Investigation-Documenter creates 2-3 design options with diagrams and text-only UX collateral, consuming `resources-investigation.md`
5. **Design Critique**: Architecture-Reviewer critiques the design for reuse, performance, scalability, and operational cost, consuming `resources-investigation.md`

**USER REVIEW GATE**: Present design options to the user. Wait for explicit approval of a
design option before proceeding to Phase 2. If user gives feedback, iterate on design.

**IMPLEMENTATION CLARIFICATION GATE** (Phase 2 entry precondition): After a design is approved
and before implementation planning, derive any unresolved, implementation-critical questions from
`design-options.md`, `ux-review.md`, and the Architecture-Reviewer output (future considerations /
open questions). Ask them as a single batched set with proposed defaults, letting the user answer,
adjust, or explicitly waive. Record the outcomes in `./docs/<feature-slug>/implementation-interview.md`,
then fold the decisions into `implementation-plan.md`. If clarification materially changes scope or
approach, return to the USER REVIEW GATE for re-approval. This gate is reachable on both the fresh
Phase 1 → Phase 2 path and direct Phase 2 resume (skip it only if a current clarification record
already exists for the latest approved design).

### Phase 2: Implementation (after user approval or direct Phase 2 resume)

See [references/feature-design-workflow.md](references/feature-design-workflow.md) for details.

4. **Implementation Plan**: Create ordered task list with dependencies
5. **Implementation**: Launch Feature-Implementer tasks (per component, respecting dependencies).
   Each Feature-Implementer outputs an **implementation summary with test specifications**.
6. **Testing (REQUIRED)**: After each Feature-Implementer task completes, you MUST launch a
   corresponding Test-Implementer task. Pass it:
   - The implementation summary and test specifications from the completed Feature-Implementer
   - The design document for behavioral expectations
   - The file paths of newly created/modified code
   Create each Test-Implementer task with `blockedBy` set to its corresponding Feature-Implementer task.
   Do NOT skip this step or proceed to validation without running tests.
7. **Validation Loop (REQUIRED)**: Run project build/test/lint, use Code-Flow-Analyzer for semantic verification, and use Feature-Validator as the final read-only gate.
   - Phase 2 cannot complete until validation runs and writes `./docs/<feature-slug>/verification.md`.
   - If validation returns `UNSATISFIED`, route targeted remediation to the correct agent and repeat implementation, testing, and validation.
   - Stop only when Feature-Validator returns `SATISFIED`, or after the bounded remediation limit is reached with unresolved findings reported.

### Output

```
./docs/<feature-slug>/
├── investigation.md
├── resources-investigation.md
├── design-options.md
├── implementation-interview.md
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
- Always run this validation step before completing Phase 2, even when resuming directly into Phase 2 from an existing design or implementation plan.
- Treat validation as a completion contract: Phase 2 exits only on `SATISFIED` from Feature-Validator, or on a bounded unresolved state that clearly lists remaining failures and owner agents.

### Cleanup
- Shut down all team agents after workflow completes
- Delete team using TeamDelete
- Remove `.tmp/` investigation artifacts from output directories
- Report final status to user
