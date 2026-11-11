# DevDude

A skill for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [GitHub Copilot coding agent](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent) that orchestrates **agent swarms** to investigate codebase architecture and implement features. Works on any codebase — it dynamically discovers project structure, modules, and conventions at runtime, then layers in UX analysis and critical architecture review where they add value.

## What It Does

DevDude provides two workflow commands and an update command accessible via `/dev-dude` in Claude Code (or as a Copilot coding agent skill):

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
6. **Fix** — Corrections and review findings are folded into the final documents; temporary artifacts are cleaned up

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

Accepts plain text descriptions, spec file paths (`.md`, `.txt`, `.pdf`, `.docx`), or one or more
image/spec paths.

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

### `update` — Update DevDude

```
/dev-dude update
```

Every launch except `update` (which runs its own pinned check) and the offline `models` commands
checks the installed root and bundled crew versions against
[JorgeRaastroem/dev-dude](https://github.com/JorgeRaastroem/dev-dude) and reports newer versions.
The read-only check is bounded to four network requests and 15 seconds, with no retries; offline
or unavailable checks warn and do not block ordinary workflows. Updates are never automatic.
Missing version/revision metadata is reported as unknown, not up to date.

`update` fetches the latest stable published GitHub release, pinned to its commit. If no release
exists, it uses the API-discovered default branch HEAD and labels it an **unreleased default-branch
build**. It updates the active root, its bundled references, the nine owned agents, and all four
functional skills in their existing installation scopes. It does not pull/reset your project or
modify unrelated agents, project files, outputs, or durable run state. Extra update arguments are
rejected; `update refresh` still refreshes an architecture vertical named `update`.

Initialization and updates do not require installation locks or cross-session lock coordination.
Updates still require quiescent controllers and descendants, including other sessions sharing global
crews. Ambiguous installation scopes,
local customizations, unverifiable legacy files, newer local versions, and permission failures
stop at explicit gates. The complete bundle is staged and
verified before replacement, with backups and whole-set rollback on failure. Installation metadata
in `<active-root>/.dev-dude-install.json` records the source SHA, versions, and owned-file hashes;
it is separate from the project's run-state `Source revision`.

After installation, DevDude reloads the session only through a supported, verified runtime operation
that rediscovers both skills and agents. If unavailable, exit and start a fresh session, then invoke
`/dev-dude` with your next command. Rereading skill files is not a reload. Update never dispatches
cached agents or automatically resumes a workflow in the old session.

## Prerequisites

| Requirement | Purpose |
|------------|---------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [GitHub Copilot coding agent](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent) | Agent runtime |
| Code-indexing MCP server | Semantic code analysis (symbol lookup, flow tracing) — see [Supported Indexers](#supported-indexers). Required on Claude Code; optional on GitHub Copilot (grep/glob/view fallback) |
| Team capability (Claude Code only) | Agent swarm orchestration (`TeamCreate` tool); GitHub Copilot has no team prerequisite |

### Supported Indexers

DevDude auto-detects available code-indexing MCP servers at startup. Claude Code requires at least
one; GitHub Copilot continues without one using grep/glob/view and records reduced confidence.

| Indexer | Repository | Capabilities |
|---------|-----------|--------------|
| [Serena](https://github.com/oraios/serena) | `oraios/serena` | list_dir, find_file, search_for_pattern, get_symbols_overview, find_symbol, find_referencing_symbols, symbol editing, project memories |
| *More indexers* | *Extend the detection rules (CTX-IDX-001) in `policies/runtime-context.yaml`* | — |

On first run, DevDude probes for known indexers, presents the detected ones to you, and lets you choose which to use. If only one is available it is auto-selected. After selection, indexer-specific onboarding is performed automatically.

### Research Sources

For feature design, DevDude separately detects available documentation MCP servers, GitHub and
package-registry lookup options, and web research tools. External claims and recommendations must
cite authoritative sources permitted by the bundled `policies/trusted-sources.yaml`; unverified
candidates cannot be recommended. Advisory checks prefer read-only sources such as GitHub Security
Advisories and OSV.

Research tools are optional. If no reliable external source is available, the resource
investigation continues with repository-local discovery and validation and records the external
research gap explicitly.

## Installation

### Execution Monitoring

DevDude selects an execution mode per invocation and records capabilities and limitations in durable
run state and stage journals:

- **Controlled:** this invocation supports verified background execution with bounded status polls
  and callable cancellation, or an enforced timeout returning control within the check interval;
  retain watchdog checks and deadline handling, verifying termination before recovery.
- **Cooperative:** neither control mechanism is usable and verified for this invocation, even if
  cancellation exists elsewhere in the runtime; dispatch through its supported mechanism without
  a cancellation-only approval gate. Work stays within its bounded objective, checkpoints progress,
  and returns partial or blocked results when appropriate. Deadlines are monitoring thresholds.

Cooperative monitoring **cannot guarantee interruption or bounded return time**. Synchronous calls
may prevent live checks; reconcile on return or resume. `deadline exceeded`, `execution status
unknown`, and `verified stopped` are distinct: elapsed time never proves cancellation. Unknown
status checkpoints uncertainty and pauses recovery, not initial dispatch. No retry, replacement
work, or overlapping writes are allowed while prior work or descendants may remain active.
After confirmed completion or termination, reconcile partial outputs and side effects before
continuing; never replay completed work. Stage boundaries, evidence validation, explicit approval
and safety gates, and the existing retry limits remain unchanged.

### Claude Code

#### Option 1: Install via Claude Code CLI

```bash
claude install-skill /path/to/dev-dude
```

#### Option 2: Manual installation

Copy the complete `Claude skill/dev-dude/` directory (not individual agents or skills) from this
repository into your Claude Code skills folder:

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

The host bootstrap installs the dedicated `dev-dude-orchestrator` with the rest of the agent crew,
then transfers control through Task. The selected agent must be able to invoke Skill, delegate
nested specialist tasks, use TeamCreate, and write authorized run outputs; host-level tool access
alone does not establish these capabilities.

### GitHub Copilot coding agent

Copy the complete `Copilot/dev-dude/` directory (not individual agents or skills) from this
repository into a Copilot skill location:

```
# User-wide
~/.copilot/skills/dev-dude/

# Or repository-local
<project>/.github/skills/dev-dude/
```

The root checks bundled agent and functional-skill versions on first run. Agents install under
`~/.copilot/agents/`; the four functional skills install atomically under `~/.copilot/skills/`.

The host bootstrap dispatches `dev-dude-orchestrator-copilot` explicitly using the orchestrator
model from the resolved model profile (the installed frontmatter model for `bundled-default`). Its invocation must support Skill, nested specialist delegation, and authorized output
writes. In either runtime, unsupported or unknown capabilities stop at an **ORCHESTRATOR CAPABILITY
GATE** with remediation, never a general-purpose fallback. Permission failures require an explicit
user decision before trying alternative methods or locations. Runtime nesting support is a
prerequisite, not a capability that these skill documents can grant.

## Skill Structure

### Claude Code (`Claude skill/dev-dude/`)

```
Claude skill/dev-dude/
├── SKILL.md                                  # Host/controller loader and step index
├── agents/                                   # Agent frontmatter + policy loader + examples
│   ├── dev-dude-orchestrator.md               #   Dedicated root workflow controller
│   ├── code-flow-analyzer.md                 #   Traces code flows, maps dependencies
│   ├── ux-design-reviewer.md                 #   Reviews UX, existing screens, and layout guidance
│   ├── architecture-reviewer.md              #   Critiques architecture and future fitness
│   ├── investigation-documenter.md           #   Creates structured docs from findings
│   ├── technical-resource-investigator.md    #   Researches and critiques reusable resources
│   ├── feature-implementer.md                #   Implements features from design specs
│   ├── test-implementer.md                   #   Writes and runs tests
│   └── feature-validator.md                  #   Gates feature completion with SATISFIED/UNSATISFIED
├── skills/                                   # Versioned, auto-installed functional skill crew
│   ├── dev-dude-architecture/                #   SKILL.md loader, references/workflow.yaml (+ workflow.md examples)
│   ├── dev-dude-feature-design/              #   SKILL.md loader, references/workflow.yaml
│   ├── dev-dude-feature-implementation/      #   SKILL.md loader, references/workflow.yaml
│   └── dev-dude-validation/                  #   SKILL.md loader, references/workflow.yaml (+ workflow.md examples)
├── policies/                                 # Normative policy YAML (see manifest.yaml)
│   ├── manifest.yaml                         #   Load sets, actor bindings, policy index
│   ├── metadata.yaml, commands.yaml, models.yaml, platform.yaml, update.yaml, install.yaml
│   ├── runtime-context.yaml, bootstrap.yaml, orchestration.yaml, state.yaml, watchdog.yaml
│   ├── handoff.yaml, stage-workflow.yaml, validation-rules.yaml, trusted-sources.yaml
│   ├── output-templates.yaml
│   └── agents/<role>.yaml                    #   One rule file per agent role
└── references/
    └── doc-format-templates.md               # Output template bodies (nonnormative)
```

### GitHub Copilot coding agent (`Copilot/dev-dude/`)

```
Copilot/dev-dude/
├── SKILL.md                                  # Host/controller loader and step index
├── agents/                                   # Agent frontmatter + policy loader + examples
│   ├── dev-dude-orchestrator-copilot.md       #   Dedicated root workflow controller
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
│   └── dev-dude-validation/                  # Each: SKILL.md loader + references/workflow.yaml
├── policies/                                 # Normative policy YAML (see manifest.yaml)
│   ├── manifest.yaml                         #   Load sets, actor bindings, policy index
│   ├── metadata.yaml, commands.yaml, models.yaml, platform.yaml, update.yaml, install.yaml
│   ├── runtime-context.yaml, bootstrap.yaml, orchestration.yaml, state.yaml, watchdog.yaml
│   ├── handoff.yaml, stage-workflow.yaml, validation-rules.yaml, trusted-sources.yaml
│   ├── output-templates.yaml
│   └── agents/<role>.yaml                    #   One rule file per agent role
└── references/
    └── doc-format-templates.md               # Output template bodies (nonnormative)
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

DevDude uses nine specialized agent types:

| Agent | Role | Used In |
|-------|------|---------|
| **DevDude-Orchestrator** | Sole root controller: reconciles evidence, validates handoffs, monitors work, and handles gates through the host | Both commands |
| **Code-Flow-Analyzer** | Traces execution flows, maps dependencies, verifies documentation accuracy | Both commands |
| **UX-Design-Reviewer** | Inspects existing UX, raw specs, and interaction flows; creates text-first UX guidance and layout maps | Both commands |
| **Architecture-Reviewer** | Critiques architecture and designs for reuse, performance, scalability, and operational cost | Both commands |
| **Investigation-Documenter** | Creates structured architecture/design documents with mermaid diagrams | Both commands |
| **Technical-Resource-Investigator** | Read-only discovery and conditional critique of reusable internal and authoritative external resources | Feature command |
| **Feature-Implementer** | Implements code changes following existing patterns and conventions | Feature command |
| **Test-Implementer** | Writes and runs tests based on implementation output | Feature command |
| **Feature-Validator** | Read-only final gate that returns SATISFIED/UNSATISFIED and targeted remediation owners | Feature command |

Agents run in parallel where possible (e.g., investigating multiple areas simultaneously) and are sequenced with dependency tracking where required (e.g., resource research consumes code-flow findings and tests are blocked by implementation). External or architecturally material resource choices receive a conditional, append-only critique pass using a stronger model. Feature implementation starts only after design approval and the Implementation Clarification Gate, then uses a bounded implementation -> testing -> validation loop. Phase 2 cannot complete until Feature-Validator returns `SATISFIED` or a bounded unresolved state is reported.

The dedicated orchestrator supplies reusable coordination expertise; the root skill defines runtime
setup, routing, global invariants, user gates, recovery, and dispatch. The `dev-dude-` agent-name
prefix deliberately avoids collisions with other orchestration agents in shared installations.
The host only bootstraps and relays exact questions and verbatim user decisions. It never writes
run outputs or state, chooses transitions, or takes over failed work. The controller skips host
bootstrap when loading the root skill, preventing recursive dispatch, and returns a structured
result rather than waiting for a human inside an invocation.

Installed functional skills return control to that dedicated root at explicit boundaries. Every
run maintains `.dev-dude-run-state.md` beside its normal outputs; the root reconciles that checkpoint
with actual documents, task results, and repository changes at command and phase entry. Delegated
tasks receive a compact orchestration envelope so their lane and completion evidence survive long
sessions and context compaction. Each functional-skill transition also creates a validated YAML
handoff under `.dev-dude-handoffs/`. A fresh stage receives only its workflow, typed contract,
authorized artifacts and tools, and evidence it retrieves itself; prior conversation is not durable
workflow state. Structural, evidence, epistemic, and workflow validation blocks unsupported,
contradictory, incomplete, or out-of-scope transitions with actionable remediation.

Controller identity and status evidence are recorded in run state. The host verifies controller
and descendant quiescence before re-entry, including after user approval; stale `active` status
alone does not prohibit recovery, and a completed status label alone does not prove termination.
Older state without the controller marker is reconciled against runtime and task evidence rather
than assumed safe. Phase workflows, output paths and retry budgets are unchanged; architecture investigation and
verification run at most 6 concurrent agents and batch the rest.

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

### Model profiles

Model commands are host-only and offline: they make no network request and never install, start,
or resume a workflow. The exact grammar is in `policies/commands.yaml` (`models_commands`):

```
/dev-dude models show
/dev-dude models profiles
/dev-dude models validate
/dev-dude models set <role|all> <model-id> --profile <name> --scope <project|user>
/dev-dude models use <profile|bundled-default> --scope <project|user>
/dev-dude models reset --scope <project|user>
```

- Config files: project `<repo>/.dev-dude/models.yaml`, user `~/.config/dev-dude/models.yaml`.
  Each holds `schema_version: "1.0"` and per-runtime namespaces (`runtimes.claude`,
  `runtimes.copilot`); a command edits only its own runtime namespace. Unknown keys, wrong types,
  other versions, aliases (such as `opus`), duplicate keys and anchors are rejected.
- `set` saves an exact model ID into a draft profile as **unvalidated**; it never activates it.
  `all` sets the nine agent roles; the `critique` role must be set explicitly. `use` activates a
  complete profile (nine roles + `critique`) or `bundled-default`.
- Resolution: an invalid config file blocks launch; otherwise the project's active profile, then the
  user's active profile, then `bundled-default`. A project file with only drafts does not hide the
  user selection; `active_profile: bundled-default` does. Profiles never merge.
- `validate` checks files offline only. Whether a model is actually usable is decided at launch by
  checking the delegation tool the current host exposes; a custom profile that cannot be verified
  stops at MODEL CAPABILITY GATE with no fallback. `bundled-default` keeps the shipped frontmatter
  models (including Claude aliases) and, for the critique pass, the legacy "verified stronger model"
  rule.
- `reset` removes only this runtime's namespace from a valid file; an invalid file is renamed to
  `models.yaml.invalid-N`.
- The resolved profile is pinned per run (`.dev-dude-model-profile.yaml` in the run output folder)
  and passed to every stage and agent; resumes use the pinned snapshot.
- Local models work only if your host runtime has registered that exact model ID and exposes it to
  the delegation tool with the tools DevDude needs; DevDude never installs, hosts, or proxies models.

### Policy files

Normative behaviour lives in YAML under each root's `policies/` (indexed by
`policies/manifest.yaml`) and in each functional skill's `references/workflow.yaml`. Markdown files
are loaders, examples and templates. Loading is instruction-driven, not enforced by a runtime.
Installation and update treat these files as owned content; model configuration files are never
touched by update.

Each complete platform bundle (root `SKILL.md`, `policies/`, `agents/`, `skills/`, `references/`) is
self-contained; individual agents and functional skills are not. They are thin loaders that resolve
the installed DevDude root and load their manifest load set, so the complete bundle is a prerequisite
even for standalone specialist use. A missing or ambiguous policy root stops at the **POLICY ROOT
GATE**; copying or installing agents or skills alone is unsupported. (This replaces the earlier
self-contained agent bodies; the decision is recorded in `policy-migration-inventory.yaml`
`migration_record.architecture_decisions`.)

During a run, the host hashes every manifest-indexed policy file with a runtime hashing tool and the
controller records them in a policy snapshot (`<run-output>/.dev-dude-policy-snapshot.yaml`). Every
resume, delegated agent and validator re-hashes the files it loads and stops at the **POLICY INTEGRITY
GATE** if a policy changed mid-run. These are instructions to the agents, not a runtime guarantee.

Check repository consistency after editing policies with `python3 scripts/policy_audit.py`.

### Agent definitions

Agent files in `.claude/agents/` (Claude Code) or `~/.copilot/agents/` (GitHub Copilot) can be customized after installation. Ordinary bootstrap preserves equal or newer installed crews and replaces missing or older crews. Explicit `update` detects changes using installation hashes and requires approval before replacing customized or unverifiable files.

### Functional skills

Installed `dev-dude-*` functional skills may be customized in their runtime skill directory. Keep a
custom skill's version equal to or newer than the bundle to prevent an older bundle replacing it;
mixed newer/older crews stop at the version-conflict gate.
Explicit `update` also gates changed files; back up customizations before approving replacement.

### Document templates

Output template bodies are in `references/doc-format-templates.md` and can be adapted to your
team's documentation standards; their required header fields and sections are the `TPL-*` rules in
`policies/output-templates.yaml`.

### Release versions

The root `SKILL.md` frontmatter `version:` is DevDude's user-facing semantic version, separate from
agent and functional-skill crew versions. Bump it manually in both platform roots for shipped bundle
changes, including root/policy changes, and bump the functional-skill crew version manually for
functional-skill changes. The `bump-agent-versions` workflow maintains only the shared agent crew
version: a push that changes `agents/*.md`, `policies/agents/*.yaml` or `policies/models.yaml` in
either bundle bumps every agent frontmatter version, the root "Bundled agent crew version" sentence
and `policies/metadata.yaml` `crews.agents.version` (declared in `metadata.yaml` `version_bump`).
Before publishing a stable release, verify both platform roots and bundled crews agree, then tag
and publish a non-draft, non-prerelease GitHub release. Launch compares numeric version tuples;
a different commit alone is not evidence of a newer release.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Generic, not repo-specific** | Works on any codebase — discovers structure dynamically via the active code indexer |
| **Configurable indexers** | Not locked to Serena — any MCP code-indexing server can be used; new indexers can be added by extending CTX-IDX-001 in `policies/runtime-context.yaml` |
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
