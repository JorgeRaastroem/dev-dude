# DevDude

A skill for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [GitHub Copilot coding agent](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent) that orchestrates **agent swarms** to investigate codebase architecture and implement features. Works on any codebase — it dynamically discovers project structure, modules, and conventions at runtime, then layers in UX analysis and critical architecture review where they add value.

## What It Does

DevDude provides two commands accessible via `/dev-dude` in Claude Code (or as a Copilot coding agent skill):

### `DudeWhereIsMyArch` — Architecture Investigation

Spawns a parallel swarm of agents to investigate your codebase and produce structured architecture documentation with mermaid diagrams.

```
/dev-dude arch all                      # Full codebase investigation
/dev-dude arch authentication           # Deep-dive into a specific area
/dev-dude where src/services/           # Investigate a directory
```

**How it works:**

1. **Discovery** — Scans your project root to identify modules, packages, tech stack, and entry points
2. **Investigation** — Launches parallel Code-Flow-Analyzer and UX-Design-Reviewer agents (one pair per area) to trace flows, inspect UX, and map dependencies
3. **Documentation** — Investigation-Documenter agents create an overview doc, per-area deep-dives, and UX collateral such as simple layout maps
4. **Verification** — Code-Flow-Analyzer agents validate every file path, symbol, and claim against actual code
5. **Critical Review** — Architecture-Reviewer critiques the mapped architecture for reuse, performance, scalability, and operational cost, then produces future considerations
6. **Fix** — Corrections and review findings are folded into the final documents; temporary artifacts are cleaned up

**Output:** `./docs/ArchOverview/` containing a high-level overview and per-area deep-dive documents.

If architecture docs already exist, requesting a specific area runs an **additive investigation** that creates a new deep-dive and updates the existing overview.

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

#### Agent auto-install

On first run, the skill checks bundled agent versions against installed agent versions (`version:` in frontmatter). Missing version is treated as `0`. If any installed agent is lower than the bundled version, the whole crew is updated atomically so all agents stay on the same version.

### GitHub Copilot coding agent

Copy the `Copilot/dev-dude/` directory from this repository into your project:

```
<project>/dev-dude/
```

On first run, the skill checks bundled agent versions against installed agent versions (`version:` in frontmatter). Missing version is treated as `0`. If any installed agent is lower than the bundled version, the whole crew is updated atomically so all agents stay on the same version.

## Skill Structure

### Claude Code (`Claude skill/dev-dude/`)

```
Claude skill/dev-dude/
├── SKILL.md                                  # Main skill (loaded when triggered)
├── agents/                                   # Bundled agent definitions
│   ├── code-flow-analyzer.md                 #   Traces code flows, maps dependencies
│   ├── ux-design-reviewer.md                 #   Reviews UX, existing screens, and layout guidance
│   ├── architecture-reviewer.md              #   Critiques architecture and future fitness
│   ├── investigation-documenter.md           #   Creates structured docs from findings
│   ├── technical-resource-investigator.md    #   Researches and critiques reusable resources
│   ├── feature-implementer.md                #   Implements features from design specs
│   ├── test-implementer.md                   #   Writes and runs tests
│   └── feature-validator.md                  #   Gates feature completion with SATISFIED/UNSATISFIED
└── references/                               # Detailed workflow guides (loaded on demand)
    ├── arch-investigation-workflow.md         #   DudeWhereIsMyArch phases
    ├── feature-design-workflow.md             #   DudeWriteMyFeature phases
    ├── doc-format-templates.md               #   Output document templates
    ├── trusted-source-policy.md              #   Authoritative research and citation policy
    └── verification-workflow.md              #   How docs are verified against code
```

### GitHub Copilot coding agent (`Copilot/dev-dude/`)

```
Copilot/dev-dude/
├── SKILL.md                                  # Main skill (loaded when triggered)
├── agents/                                   # Bundled agent definitions
│   ├── code-flow-analyzer-copilot.md         #   Traces code flows, maps dependencies
│   ├── ux-design-reviewer-copilot.md         #   Reviews UX, existing screens, and layout guidance
│   ├── architecture-reviewer-copilot.md      #   Critiques architecture and future fitness
│   ├── investigation-documenter-copilot.md   #   Creates structured docs from findings
│   ├── technical-resource-investigator-copilot.md # Researches and critiques reusable resources
│   ├── feature-implementer-copilot.md        #   Implements features from design specs
│   ├── test-implementer-copilot.md           #   Writes and runs tests
│   └── feature-validator-copilot.md          #   Gates feature completion with SATISFIED/UNSATISFIED
└── references/                               # Detailed workflow guides (loaded on demand)
    ├── argument-parsing.md                   #   Command routing, aliases, and usage text
    ├── arch-investigation-workflow.md         #   DudeWhereIsMyArch phases
    ├── feature-design-workflow.md             #   DudeWriteMyFeature phases
    ├── doc-format-templates.md               #   Output document templates
    ├── trusted-source-policy.md              #   Authoritative research and citation policy
    └── verification-workflow.md              #   How docs are verified against code
```

After installation the agent definitions are placed in the runtime-specific agents folder:

| Runtime | Agents folder |
|---------|--------------|
| Claude Code | `.claude/agents/` |
| GitHub Copilot coding agent | `~/.copilot/agents/` |

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
| **Progressive disclosure** | SKILL.md stays lean; detailed workflows live in reference files loaded on demand |
| **`$INDEXER_CONTEXT` injection** | Agents receive a structured description of active indexer tools via task prompts so they can adapt to any indexer without hardcoded tool names |
| **`$RESOURCE_RESEARCH_CONTEXT` injection** | Resource investigation receives a separate inventory of available research tools and degrades explicitly to repository-local work when needed |

## License

MIT
