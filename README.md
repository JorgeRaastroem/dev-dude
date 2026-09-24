# DevDude

A skill for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [GitHub Copilot coding agent](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent) that orchestrates **agent swarms** to investigate codebase architecture and implement features. Works on any codebase — it dynamically discovers project structure, modules, and conventions at runtime, then layers in UX analysis and critical architecture review where they add value.

## What It Does

DevDude provides two commands accessible via `/dev-dude` in Claude Code (or as a Copilot coding agent skill):

### `DudeWhereIsMyArch` — Architecture Investigation

Spawns a parallel swarm of agents to investigate your codebase and produce structured architecture documentation with mermaid diagrams.

```
/dev-dude arch all                      # Full codebase investigation
/dev-dude all refresh                   # Refresh all affected docs and discover new verticals
/dev-dude authentication refresh        # Refresh one architecture vertical
/dev-dude arch authentication           # Deep-dive into a specific area
/dev-dude where src/services/           # Investigate a directory
```

**How it works:**

1. **Discovery** — Scans your project root to identify modules, packages, tech stack, and entry points
2. **Investigation** — Launches parallel Code-Flow-Analyzer and UX-Design-Reviewer agents (one pair per area) to trace flows, inspect UX, and map dependencies
3. **Documentation** — Investigation-Documenter agents create an overview doc, per-area deep-dives, and UX collateral such as simple layout maps
4. **Verification** — Code-Flow-Analyzer agents validate every file path, symbol, and claim against actual code
5. **Critical Review** — Architecture-Reviewer critiques the mapped architecture for reuse, performance, scalability, and operational cost, then produces future considerations
6. **Fix** — Corrections and review findings are folded into final documents; run-owned temporary
   artifacts are cleaned only after output validation and a durable run-state checkpoint

**Output:** `./docs/ArchOverview/` containing a high-level overview and per-area deep-dive documents.

If architecture docs already exist, requesting a specific area runs an **additive investigation** that creates a new deep-dive and updates the existing overview. Use `all refresh` on the current `main` or `master` branch to compare it with the source commits of the existing documents, refresh only affected deep-dives, and create documentation for newly introduced architecture areas. Use `<vertical> refresh` to limit that refresh to one architecture vertical and its overview references.

### `DudeWriteMyFeature` — Feature Design & Implementation

Designs and implements features through codebase investigation, authoritative resource research,
design review, implementation clarification, and a bounded validation loop.

```
/dev-dude feature Add user profile caching
/dev-dude write ./specs/my-feature.md
/dev-dude feature ./mockups/new-dashboard.png
```

Accepts plain text descriptions, spec file paths (`.md`, `.txt`, `.pdf`), or image paths.

**How it works:**

| Phase | What Happens | Agents Used |
|-------|-------------|-------------|
| Investigation | Analyze existing code flows and relevant UX patterns for the feature | Code-Flow-Analyzer, UX-Design-Reviewer |
| Resource Investigation | Validate internal reuse candidates and research external packages, services, platforms, and APIs from authoritative sources | Technical-Resource-Investigator |
| Resource Critique (conditional) | Pressure-test material candidates for security, reliability, maintenance, licensing, supply-chain risk, and operational cost | Technical-Resource-Investigator (stronger-model pass) |
| Design Options | Generate 2-3 design options with diagrams, UX guidance, and trade-offs | Investigation-Documenter |
| Architecture Critique | Critique the design for reuse, performance, scalability, and operational cost | Architecture-Reviewer |
| **User Review** | **You pick a design option before implementation begins** | — |
| **Implementation Clarification** | **Resolve or explicitly waive implementation-critical questions before planning; material changes return to User Review** | — |
| Implementation Planning | Fold the approved design and clarification decisions into the implementation plan | — |
| Implementation | Build the feature per the approved design | Feature-Implementer(s) |
| Testing | Write and run tests based on implementation output | Test-Implementer(s) |
| Validation Loop | Run build/test/lint, verify implementation flow, gate on SATISFIED, and route targeted remediation until satisfied or bounded unresolved | Code-Flow-Analyzer, Feature-Validator |

**Output:** `./docs/<feature-slug>/` containing `investigation.md`,
`resources-investigation.md`, `design-options.md`, `implementation-interview.md`,
`implementation-plan.md`, and `verification.md`.

## Prerequisites

| Requirement | Purpose |
|------------|---------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [GitHub Copilot coding agent](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent) | Agent runtime |
| Code-indexing MCP server | Semantic code analysis (symbol lookup, flow tracing) — see [Supported Indexers](#supported-indexers) |
| Team capability | Agent swarm orchestration (`TeamCreate` tool) |

### Supported Indexers

DevDude auto-detects available code-indexing MCP servers at startup. At least one is required.

| Indexer | Repository | Capabilities |
|---------|-----------|--------------|
| [Serena](https://github.com/oraios/serena) | `oraios/serena` | list_dir, find_file, search_for_pattern, get_symbols_overview, find_symbol, find_referencing_symbols, symbol editing, project memories |
| *More indexers* | *Extend the detection table in `SKILL.md`* | — |

On first run, DevDude probes for known indexers, presents the detected ones to you, and lets you choose which to use. If only one is available it is auto-selected. After selection, indexer-specific onboarding is performed automatically.

### Research Sources

For feature design, DevDude separately detects available documentation MCP servers, GitHub and
package-registry lookup options, and web research tools. External claims and recommendations must
cite authoritative sources permitted by the bundled `trusted-source-policy.md`; unverified
candidates cannot be recommended. Advisory checks prefer read-only sources such as GitHub Security
Advisories and OSV.

Research tools are optional. If no reliable external source is available, the resource
investigation continues with repository-local discovery and validation and records the external
research gap explicitly.

## Installation

### Claude Code

#### Option 1: Install via Claude Code CLI

```bash
claude install-skill /path/to/dev-dude
```

#### Option 2: Manual installation

Copy the `Claude skill/dev-dude/` directory from this repository into your Claude Code skills folder:

```
# Global (available in all projects)
~/.claude/skills/dev-dude/

# Or project-local
<project>/.claude/skills/dev-dude/
```

#### Bundled crew auto-install

On first run, the root checks both bundled agent and functional-skill versions. Missing versions are
treated as `0`. If any functional skill is missing or older, all four sibling skills are installed
or updated atomically beside the active root skill.

### GitHub Copilot coding agent

Copy the `Copilot/dev-dude/` directory from this repository into a Copilot skill location:

```
# User-wide
~/.copilot/skills/dev-dude/

# Or repository-local
<project>/.github/skills/dev-dude/
```

The root checks bundled agent and functional-skill versions on first run. Agents install under
`~/.copilot/agents/`; the four functional skills install atomically under `~/.copilot/skills/`.

## Skill Structure

### Claude Code (`Claude skill/dev-dude/`)

```
Claude skill/dev-dude/
├── SKILL.md                                  # Thin root orchestrator (loaded when triggered)
├── agents/                                   # Bundled agent definitions
│   ├── code-flow-analyzer.md                 #   Traces code flows, maps dependencies
│   ├── ux-design-reviewer.md                 #   Reviews UX, existing screens, and layout guidance
│   ├── architecture-reviewer.md              #   Critiques architecture and future fitness
│   ├── investigation-documenter.md           #   Creates structured docs from findings
│   ├── technical-resource-investigator.md    #   Researches and critiques reusable resources
│   ├── feature-implementer.md                #   Implements features from design specs
│   ├── test-implementer.md                   #   Writes and runs tests
│   └── feature-validator.md                  #   Gates feature completion with SATISFIED/UNSATISFIED
├── skills/                                   # Versioned, auto-installed functional skill crew
│   ├── dev-dude-architecture/
│   │   ├── SKILL.md
│   │   └── references/workflow.md
│   ├── dev-dude-feature-design/
│   │   ├── SKILL.md
│   │   └── references/workflow.md
│   ├── dev-dude-feature-implementation/
│   │   ├── SKILL.md
│   │   └── references/workflow.md
│   └── dev-dude-validation/
│       ├── SKILL.md
│       └── references/workflow.md
└── references/                               # Root orchestration contracts and shared policies
    ├── orchestration-state.md
    ├── stage-workflow.md
    ├── handoff-contract-schema.md
    ├── validation-rules.md
    ├── doc-format-templates.md
    └── trusted-source-policy.md
```

### GitHub Copilot coding agent (`Copilot/dev-dude/`)

```
Copilot/dev-dude/
├── SKILL.md                                  # Thin root orchestrator (loaded when triggered)
├── agents/                                   # Bundled agent definitions
│   ├── code-flow-analyzer-copilot.md         #   Traces code flows, maps dependencies
│   ├── ux-design-reviewer-copilot.md         #   Reviews UX, existing screens, and layout guidance
│   ├── architecture-reviewer-copilot.md      #   Critiques architecture and future fitness
│   ├── investigation-documenter-copilot.md   #   Creates structured docs from findings
│   ├── technical-resource-investigator-copilot.md # Researches and critiques reusable resources
│   ├── feature-implementer-copilot.md        #   Implements features from design specs
│   ├── test-implementer-copilot.md           #   Writes and runs tests
│   └── feature-validator-copilot.md          #   Gates feature completion with SATISFIED/UNSATISFIED
├── skills/                                   # Versioned, auto-installed functional skill crew
│   ├── dev-dude-architecture/
│   ├── dev-dude-feature-design/
│   ├── dev-dude-feature-implementation/
│   └── dev-dude-validation/                  # Each contains SKILL.md + references/workflow.md
└── references/                               # Root orchestration contracts and shared policies
    ├── argument-parsing.md
    ├── orchestration-state.md
    ├── stage-workflow.md
    ├── handoff-contract-schema.md
    ├── validation-rules.md
    ├── doc-format-templates.md
    └── trusted-source-policy.md
```

After installation the agent definitions are placed in the runtime-specific agents folder:

| Runtime | Agents folder |
|---------|--------------|
| Claude Code | `.claude/agents/` |
| GitHub Copilot coding agent | `~/.copilot/agents/` |

The functional skills are installed as discoverable siblings:

| Runtime | Functional skill folder |
|---------|-------------------------|
| Claude Code project scope | `<project>/.claude/skills/<skill-name>/` |
| Claude Code user scope | `~/.claude/skills/<skill-name>/` |
| GitHub Copilot | `~/.copilot/skills/<skill-name>/` |

## Agent Swarm Architecture

DevDude orchestrates eight specialized agent types:

| Agent | Role | Used In |
|-------|------|---------|
| **Code-Flow-Analyzer** | Traces execution flows, maps dependencies, verifies documentation accuracy | Both commands |
| **UX-Design-Reviewer** | Inspects existing UX, raw specs, and interaction flows; creates text-first UX guidance and layout maps | Both commands |
| **Architecture-Reviewer** | Critiques architecture and designs for reuse, performance, scalability, and operational cost | Both commands |
| **Investigation-Documenter** | Creates structured architecture/design documents with mermaid diagrams | Both commands |
| **Technical-Resource-Investigator** | Read-only discovery and conditional critique of reusable internal and authoritative external resources | Feature command |
| **Feature-Implementer** | Implements code changes following existing patterns and conventions | Feature command |
| **Test-Implementer** | Writes and runs tests based on implementation output | Feature command |
| **Feature-Validator** | Read-only final gate that returns SATISFIED/UNSATISFIED and targeted remediation owners | Feature command |

Agents run in parallel where possible (e.g., investigating multiple areas simultaneously) and are sequenced with dependency tracking where required (e.g., resource research consumes code-flow findings and tests are blocked by implementation). External or architecturally material resource choices receive a conditional, append-only critique pass using a stronger model. Feature implementation starts only after design approval and the Implementation Clarification Gate, then uses a bounded implementation -> testing -> validation loop. Phase 2 cannot complete until Feature-Validator returns `SATISFIED` or a bounded unresolved state is reported.

The root skill is intentionally limited to runtime setup, routing, global invariants, user gates,
recovery, and dispatch. Installed functional skills return control at explicit boundaries. Every
run maintains `.dev-dude-run-state.md` beside its normal outputs; the root reconciles that checkpoint
with actual documents, task results, and repository changes at command and phase entry. Delegated
tasks receive a compact orchestration envelope so their lane and completion evidence survive long
sessions and context compaction. Each functional-skill transition also creates a validated YAML
handoff under `.dev-dude-handoffs/`. A fresh stage receives only its workflow, typed contract,
authorized artifacts and tools, and evidence it retrieves itself; prior conversation is not durable
workflow state. Structural, evidence, epistemic, and workflow validation blocks unsupported,
contradictory, incomplete, or out-of-scope transitions with actionable remediation.

```
DudeWhereIsMyArch "all"
│
├─ Phase 1: Investigation (parallel)
│  ├─ Code-Flow-Analyzer → area-1
│  ├─ UX-Design-Reviewer → area-1
│  ├─ Code-Flow-Analyzer → area-N
│  └─ UX-Design-Reviewer → area-N
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
├─ Phase 4: Critical review (blocked by Phase 3)
│  └─ Architecture-Reviewer → future considerations + critique
│
└─ Phase 5: Fix (blocked by Phase 4)
   └─ Investigation-Documenter → apply corrections
```

```
DudeWriteMyFeature "<feature>"
│
├─ Investigation → Code-Flow-Analyzer + UX-Design-Reviewer
├─ Resource investigation → Technical-Resource-Investigator
├─ Resource critique (conditional) → stronger-model Technical-Resource-Investigator
├─ Design options → Investigation-Documenter
├─ Architecture critique → Architecture-Reviewer
├─ User review gate → approve a design
├─ Implementation clarification gate → answer or waive unresolved decisions
├─ Implementation planning → approved design + clarification decisions
├─ Implementation + testing → Feature-Implementer + Test-Implementer
└─ Validation loop → Code-Flow-Analyzer + Feature-Validator
```

## Output Format

All documents use consistent templates with:

- Metadata headers (date, scope, tech stack)
- Mermaid diagrams for architecture and data flows
- Optional text-first UX collateral such as simple layout maps
- File path references for every code mention
- Cross-references between related documents
- Glossary of domain-specific terms
- Allowlisted citations for external resource facts and recommendations
- Append-only critique sections that preserve first-pass evidence and provenance

## Customization

### Agent definitions

Agent files in `.claude/agents/` (Claude Code) or `~/.copilot/agents/` (GitHub Copilot) can be customized after installation. The skill won't overwrite existing agent files on subsequent runs.

### Functional skills

Installed `dev-dude-*` functional skills may be customized in their runtime skill directory. Keep a
custom skill's version equal to or newer than the bundle to prevent an older bundle replacing it;
mixed newer/older crews stop at the version-conflict gate.

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
| **Implementation clarification gate** | Resolves or explicitly waives implementation-critical ambiguity before planning; material changes require renewed design approval |
| **Trusted-source enforcement** | External resource recommendations require allowlisted authoritative citations; unsupported candidates remain unverified |
| **Provenance-preserving critique** | Conditional resource critique appends amendments without deleting the discovery pass's evidence or citations |
| **One-pass verification** | Verifies docs once and applies fixes — no infinite re-verification loops |
| **Progressive disclosure** | The root SKILL.md stays lean and invokes only the installed functional skill needed for the reconciled state |
| **Atomic skill crew** | Four versioned functional skills are staged, verified, and installed together so workflow ownership cannot drift |
| **Durable orchestration state** | Phase, task, gate, and transition checkpoints are reconciled with real outputs before a compacted or resumed run continues |
| **Orchestration envelope** | Every delegated task receives its run state, workflow block, lane, expected output, completion evidence, and next owner |
| **`$INDEXER_CONTEXT` injection** | Agents receive a structured description of active indexer tools via task prompts so they can adapt to any indexer without hardcoded tool names |
| **`$RESOURCE_RESEARCH_CONTEXT` injection** | Resource investigation receives a separate inventory of available research tools and degrades explicitly to repository-local work when needed |

## License

MIT
