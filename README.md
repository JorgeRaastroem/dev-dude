# DevDude

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that orchestrates **agent swarms** to investigate codebase architecture and implement features. Works on any codebase — it dynamically discovers project structure, modules, and conventions at runtime.

## What It Does

DevDude provides two commands accessible via `/dev-dude` in Claude Code:

### `DudeWhereIsMyArch` — Architecture Investigation

Spawns a parallel swarm of agents to investigate your codebase and produce structured architecture documentation with mermaid diagrams.

```
/dev-dude arch all                      # Full codebase investigation
/dev-dude arch authentication           # Deep-dive into a specific area
/dev-dude where src/services/           # Investigate a directory
```

**How it works:**

1. **Discovery** — Scans your project root to identify modules, packages, tech stack, and entry points
2. **Investigation** — Launches parallel Code-Flow-Analyzer agents (one per area) to trace flows and map dependencies
3. **Documentation** — Investigation-Documenter agents create an overview doc and per-area deep-dives
4. **Verification** — Code-Flow-Analyzer agents validate every file path, symbol, and claim against actual code
5. **Fix** — Corrections are applied automatically; temporary artifacts are cleaned up

**Output:** `./docs/ArchOverview/` containing a high-level overview and per-area deep-dive documents.

If architecture docs already exist, requesting a specific area runs an **additive investigation** that creates a new deep-dive and updates the existing overview.

### `DudeWriteMyFeature` — Feature Design & Implementation

Designs and implements features with a user review gate between design and implementation.

```
/dev-dude feature Add user profile caching
/dev-dude write ./specs/my-feature.md
/dev-dude feature ./mockups/new-dashboard.png
```

Accepts plain text descriptions, spec file paths (`.md`, `.txt`, `.pdf`), or image paths.

**How it works:**

| Phase | What Happens | Agents Used |
|-------|-------------|-------------|
| Investigation | Analyze existing code flows related to the feature | Code-Flow-Analyzer |
| Design Options | Generate 2-3 design options with diagrams and trade-offs | Investigation-Documenter |
| **User Review** | **You pick a design option before implementation begins** | — |
| Implementation | Build the feature per the approved design | Feature-Implementer(s) |
| Testing | Write and run tests based on implementation output | Test-Implementer(s) |
| Validation | Run build/test/lint + verify implementation matches spec | Code-Flow-Analyzer |

**Output:** `./docs/<feature-slug>/` containing investigation notes, design options, implementation plan, and verification report.

## Prerequisites

| Requirement | Purpose |
|------------|---------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | CLI agent runtime |
| Code-indexing MCP server | Semantic code analysis (symbol lookup, flow tracing) — see [Supported Indexers](#supported-indexers) |
| Team capability | Agent swarm orchestration (`TeamCreate` tool) |

### Supported Indexers

DevDude auto-detects available code-indexing MCP servers at startup. At least one is required.

| Indexer | Repository | Capabilities |
|---------|-----------|--------------|
| [Serena](https://github.com/oraios/serena) | `oraios/serena` | list_dir, find_file, search_for_pattern, get_symbols_overview, find_symbol, find_referencing_symbols, symbol editing, project memories |
| *More indexers* | *Extend the detection table in `SKILL.md`* | — |

On first run, DevDude probes for known indexers, presents the detected ones to you, and lets you choose which to use. If only one is available it is auto-selected. After selection, indexer-specific onboarding is performed automatically.

## Installation

### Option 1: Install via Claude Code CLI

```bash
claude install-skill /path/to/dev-dude
```

### Option 2: Manual installation

Copy the `dev-dude/` directory into your Claude Code skills folder:

```
# Global (available in all projects)
~/.claude/skills/dev-dude/

# Or project-local
<project>/.claude/skills/dev-dude/
```

### Agent auto-install

On first run, the skill automatically copies its bundled agent definitions from `agents/` into `.claude/agents/`, making them available as Task tool subagent types. Existing agent files are not overwritten.

## Skill Structure

```
dev-dude/
├── SKILL.md                                  # Main skill (loaded when triggered)
├── agents/                                   # Bundled agent definitions
│   ├── code-flow-analyzer.md                 #   Traces code flows, maps dependencies
│   ├── investigation-documenter.md           #   Creates structured docs from findings
│   ├── feature-implementer.md                #   Implements features from design specs
│   └── test-implementer.md                   #   Writes and runs tests
└── references/                               # Detailed workflow guides (loaded on demand)
    ├── arch-investigation-workflow.md         #   DudeWhereIsMyArch phases
    ├── feature-design-workflow.md             #   DudeWriteMyFeature phases
    ├── doc-format-templates.md               #   Output document templates
    └── verification-workflow.md              #   How docs are verified against code
```

## Agent Swarm Architecture

DevDude orchestrates four specialized agent types:

| Agent | Role | Used In |
|-------|------|---------|
| **Code-Flow-Analyzer** | Traces execution flows, maps dependencies, verifies documentation accuracy | Both commands |
| **Investigation-Documenter** | Creates structured architecture/design documents with mermaid diagrams | Both commands |
| **Feature-Implementer** | Implements code changes following existing patterns and conventions | Feature command |
| **Test-Implementer** | Writes and runs tests based on implementation output | Feature command |

Agents run in parallel where possible (e.g., investigating multiple areas simultaneously) and are sequenced with dependency tracking where required (e.g., tests blocked by implementation).

```
DudeWhereIsMyArch "all"
│
├─ Phase 1: Investigation (parallel)
│  ├─ Code-Flow-Analyzer → area-1
│  ├─ Code-Flow-Analyzer → area-2
│  └─ Code-Flow-Analyzer → area-N
│
├─ Phase 2: Documentation (blocked by Phase 1)
│  ├─ Investigation-Documenter → overview doc
│  ├─ Investigation-Documenter → area-1 deep-dive
│  └─ Investigation-Documenter → area-N deep-dive
│
├─ Phase 3: Verification (blocked by Phase 2)
│  ├─ Code-Flow-Analyzer → verify overview
│  └─ Code-Flow-Analyzer → verify each deep-dive
│
└─ Phase 4: Fix (blocked by Phase 3)
   └─ Investigation-Documenter → apply corrections
```

## Output Format

All documents use consistent templates with:

- Metadata headers (date, scope, tech stack)
- Mermaid diagrams for architecture and data flows
- File path references for every code mention
- Cross-references between related documents
- Glossary of domain-specific terms

## Customization

### Agent definitions

Agent files in `.claude/agents/` can be customized after installation. The skill won't overwrite existing agent files on subsequent runs.

### Document templates

Output templates are defined in `references/doc-format-templates.md` and can be modified to match your team's documentation standards.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Generic, not repo-specific** | Works on any codebase — discovers structure dynamically via the active code indexer |
| **Configurable indexers** | Not locked to Serena — any MCP code-indexing server can be used; new indexers can be added by extending the detection table in `SKILL.md` |
| **Dynamic area discovery** | No hardcoded module lists; reads project manifests and directory structure |
| **Build/test command discovery** | Reads `package.json`, `Makefile`, `Cargo.toml` etc. to find the right commands |
| **User review gate** | Prevents wasted implementation effort by getting design approval first |
| **One-pass verification** | Verifies docs once and applies fixes — no infinite re-verification loops |
| **Progressive disclosure** | SKILL.md stays lean; detailed workflows live in reference files loaded on demand |
| **`$INDEXER_CONTEXT` injection** | Agents receive a structured description of active indexer tools via task prompts so they can adapt to any indexer without hardcoded tool names |

## License

MIT
