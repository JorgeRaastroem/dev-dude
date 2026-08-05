---
name: dev-dude
description: >
  Architecture investigation and feature implementation using agent fleets.
  Works on any codebase by dynamically discovering project structure, areas, and conventions.
  Commands: DudeWhereIsMyArch (arch/where) performs parallel architecture investigation and writes
  docs to ./docs/ArchOverview/. DudeWriteMyFeature (feature/write) designs and implements features
  with a user review gate, accepting text prompts, spec files, or image inputs and writing outputs
  to ./docs/<feature-slug>/. Requires at least one code-indexing MCP server, Mermaid tooling, and
  the bundled fleet agents.
---
argument-hint:
  - "DudeWhereIsMyArch all" — Full codebase architecture investigation
  - "DudeWhereIsMyArch authentication" — Deep-dive into authentication area
  - "DudeWhereIsMyArch src/services/" — Investigate specific directory
  - "DudeWriteMyFeature Add user caching" — Implement feature from description
  - "DudeWriteMyFeature ./specs/my-feature.md" — Implement from spec document
  - "DudeWriteMyFeature ./images/feature-spec.png" — Implement from visual spec

# DevDude

Architecture investigation and feature implementation powered by agent fleets.

## 1. Prerequisites

### Install Agents

Copy agent definitions from this skill's `agents/` directory to `~/.copilot/agents/` so they
become available as custom agent types for the Task tool.

Bundled agent crew version: `1.0.4` (all agents must always use the same version).

```
Skill path: <skill-path>/agents/
Target: ~/.copilot/agents/

Files to install:
  code-flow-analyzer-copilot.md    → ~/.copilot/agents/code-flow-analyzer-copilot.md
  ux-design-reviewer-copilot.md    → ~/.copilot/agents/ux-design-reviewer-copilot.md
  architecture-reviewer-copilot.md → ~/.copilot/agents/architecture-reviewer-copilot.md
  technical-resource-investigator-copilot.md → ~/.copilot/agents/technical-resource-investigator-copilot.md
  investigation-documenter-copilot.md → ~/.copilot/agents/investigation-documenter-copilot.md
  feature-implementer-copilot.md   → ~/.copilot/agents/feature-implementer-copilot.md
  test-implementer-copilot.md      → ~/.copilot/agents/test-implementer-copilot.md
  feature-validator-copilot.md     → ~/.copilot/agents/feature-validator-copilot.md
```

For each file: compare the bundled version with the installed version in
`~/.copilot/agents/<name>.md` frontmatter (`version:`).

Rules:
- If installed file is missing, copy bundled file.
- If installed file has no `version`, treat it as `0`.
- If installed version is lower than bundled version, overwrite with bundled file (update).
- If installed version is equal or higher, keep installed file (do not overwrite).

Always update all agent files as one atomic set when any installed version is lower so the crew
remains on one shared version.

### Install Mermaid Validation Tooling

Install Mermaid CLI so investigation-documenter-copilot can validate Mermaid diagrams with parser and render checks:

```bash
npm install --global @mermaid-js/mermaid-cli
```

If CLI installation is not possible in the environment, ensure a Mermaid parser/library fallback is available and require explicit reporting that CLI validation was unavailable.

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

### Verify Agent Crew

Confirm all 8 custom agent types are available via the Task tool:
- `code-flow-analyzer-copilot`
- `ux-design-reviewer-copilot`
- `architecture-reviewer-copilot`
- `technical-resource-investigator-copilot`
- `investigation-documenter-copilot`
- `feature-implementer-copilot`
- `test-implementer-copilot`
- `feature-validator-copilot`

If any are missing, attempt to install them from this skill's `agents/` directory.

### Normalize Task Model Selection

Every `task` tool call MUST pass the selected agent's frontmatter `model` alias in the runtime's
separate `model` and `reasoning_effort` fields:

- If the alias ends in a reasoning-effort suffix (`minimal`, `low`, `medium`, `high`, `xhigh`, or
  `max`), remove that suffix from `model` and pass it as `reasoning_effort`.
- If the alias has no reasoning-effort suffix, pass the full alias as `model` and omit
  `reasoning_effort`.
- Apply the same normalization to explicit model overrides. Never pass a combined alias as the
  task's `model` value.

For example, frontmatter `model: gpt-5.6-luna-high` becomes:

```
model: "gpt-5.6-luna"
reasoning_effort: "high"
```

### Load Project Context

If a code indexer is available, use it to load project context. For example, with Serena:
```
list_memories()
→ Read any relevant memories (project_overview, style_and_conventions, etc.)
```
Other indexers: use their equivalent context/memory retrieval tools.

If no prerequisite fails critically, print the error with remediation steps and stop.

## 2. Argument Parsing

Parse `$ARGUMENTS` using the command routing rules in
[references/argument-parsing.md](references/argument-parsing.md).

In short:
- `DudeWhereIsMyArch`, `arch`, `where` → Architecture Investigation
- `DudeWriteMyFeature`, `feature`, `write` → Feature Design & Implementation
- Remaining tokens after the command are passed through as that command's argument.

## 3. DudeWhereIsMyArch

Investigates and documents codebase architecture using parallel agent fleets.

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

### Fleet Execution

For architecture work, run a fleet using the bundled agents:
- `code-flow-analyzer-copilot`
- `ux-design-reviewer-copilot`
- `architecture-reviewer-copilot`
- `investigation-documenter-copilot`

**IMPORTANT**: When creating any agent task, always include `$INDEXER_CONTEXT` in the task
prompt so agents know which code indexer tools are available.

Use the `task` tool to launch agents. For parallel execution, use `mode: "background"` and
then `read_agent(wait: true)` for each agent to wait for completion before starting the next
phase. For sequential execution within a phase, use `mode: "sync"`.

See [references/arch-investigation-workflow.md](references/arch-investigation-workflow.md) for
detailed phase-by-phase workflow including:
- Phase 1: Parallel investigation (code-flow-analyzer-copilot + ux-design-reviewer-copilot per area, background mode)
- Phase 2: Documentation (investigation-documenter-copilot creates overview + deep-dives + UX collateral)
- Phase 3: Verification (code-flow-analyzer-copilot validates docs against code)
- Phase 4: Critical review (architecture-reviewer-copilot critiques the mapped architecture)
- Phase 5: Fix application (investigation-documenter-copilot applies corrections and future considerations)

### Output

```
./docs/ArchOverview/
├── <project>-architecture-overview.md    # High-level overview
├── <project>-<area-1>.md                 # Deep-dive per area
├── <project>-<area-2>.md
└── ...
```

## 4. DudeWriteMyFeature

Designs and implements features using agent fleets with a user review gate.

For feature work, run a fleet using all bundled agents:
- `code-flow-analyzer-copilot`
- `ux-design-reviewer-copilot`
- `architecture-reviewer-copilot`
- `technical-resource-investigator-copilot`
- `investigation-documenter-copilot`
- `feature-implementer-copilot`
- `test-implementer-copilot`
- `feature-validator-copilot`

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
`$INDEXER_CONTEXT` and `$RESOURCE_RESEARCH_CONTEXT` to the technical-resource-investigator-copilot
tasks (Steps 1.5 and 1.6).

See [references/feature-design-workflow.md](references/feature-design-workflow.md) for details.

1. **Investigation**: code-flow-analyzer-copilot and ux-design-reviewer-copilot investigate relevant existing flows and UX constraints (sync)
2. **Resource Investigation (Step 1.5)**: technical-resource-investigator-copilot (mode `discovery`) consumes `investigation.md`, validates reuse candidates, and identifies authoritative external resources with allowlisted citations → `resources-investigation.md` (sync)
3. **Resource Critique (Step 1.6, conditional)**: a second technical-resource-investigator-copilot pass (mode `critique-and-amend`, stronger model override) critiques external/material candidates for security, reliability, maintenance, licensing, supply-chain risk, and operational cost, appending amendments without overwriting evidence. Skipped (with reason recorded) when no external or material candidates exist (sync)
4. **Design Options**: investigation-documenter-copilot creates 2-3 design options with diagrams and text-only UX collateral, consuming `resources-investigation.md` (sync)
5. **Design Critique**: architecture-reviewer-copilot critiques the design for reuse, performance, scalability, and operational cost, consuming `resources-investigation.md` (sync)

**USER REVIEW GATE**: Present design options to the user. Wait for explicit approval of a
design option before proceeding to Phase 2. If user gives feedback, iterate on design.

**IMPLEMENTATION CLARIFICATION GATE** (Phase 2 entry precondition): After a design is approved
and before implementation planning, derive any unresolved, implementation-critical questions from
`design-options.md`, `ux-review.md`, and the architecture review (future considerations / open
questions). Ask them as a single batched set with proposed defaults, letting the user answer,
adjust, or explicitly waive. Record the outcomes in `./docs/<feature-slug>/implementation-interview.md`,
then fold the decisions into `implementation-plan.md`. If clarification materially changes scope or
approach, return to the USER REVIEW GATE for re-approval. This gate is reachable on both the fresh
Phase 1 → Phase 2 path and direct Phase 2 resume (skip it only if a current clarification record
already exists for the latest approved design).

### Phase 2: Implementation (after user approval or direct Phase 2 resume)

See [references/feature-design-workflow.md](references/feature-design-workflow.md) for details.

4. **Implementation Plan**: Create ordered task list with dependencies
5. **Implementation**: Launch feature-implementer-copilot tasks (per component, respecting dependencies).
   - Independent components: `mode: "background"` (max 3 concurrent)
   - Dependent components: `mode: "sync"` or wait for background tasks first
   Each feature-implementer-copilot outputs an **implementation summary with test specifications**.
6. **Testing (REQUIRED)**: After each feature-implementer-copilot task completes, you MUST launch a
   corresponding test-implementer-copilot task. Pass it:
   - The implementation summary and test specifications from the completed feature-implementer
   - The design document for behavioral expectations
   - The file paths of newly created/modified code
   Do NOT skip this step or proceed to validation without running tests.
7. **Validation Loop (REQUIRED)**: Run project build/test/lint, use code-flow-analyzer-copilot for semantic verification, and use feature-validator-copilot as the final read-only gate.
   - Phase 2 cannot complete until validation runs and writes `./docs/<feature-slug>/verification.md`.
   - If validation returns `UNSATISFIED`, route targeted remediation to the correct agent and repeat implementation, testing, and validation.
   - Stop only when feature-validator-copilot returns `SATISFIED`, or after the bounded remediation limit is reached with unresolved findings reported.

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

All documents must follow
[references/doc-format-templates.md](references/doc-format-templates.md), including metadata
headers, mermaid diagrams, file path references, cross-references, and overview glossaries.

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
- Always run this validation step before completing Phase 2, even when resuming directly into Phase 2 from an existing design or implementation plan.
- Treat validation as a completion contract: Phase 2 exits only on `SATISFIED` from feature-validator-copilot, or on a bounded unresolved state that clearly lists remaining failures and owner agents.

### Cleanup
- Remove `.tmp/` investigation artifacts from output directories
- Report final status to user
