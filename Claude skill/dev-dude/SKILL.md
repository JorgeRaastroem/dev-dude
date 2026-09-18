---
name: dev-dude
description: >
  Resumable architecture investigation and feature implementation using agent swarms.
  DudeWhereIsMyArch (arch/where) writes architecture docs to ./docs/ArchOverview/.
  DudeWriteMyFeature (feature/write) accepts descriptions, specs, or images and writes design,
  implementation, and verification outputs to ./docs/<feature-slug>/.
---
argument-hint:
  - "DudeWhereIsMyArch all" — Full architecture investigation
  - "all refresh" — Refresh affected architecture docs
  - "authentication refresh" — Refresh one architecture vertical
  - "DudeWhereIsMyArch authentication" — Investigate one area
  - "DudeWriteMyFeature Add user caching" — Design and implement a feature

# DevDude Root Orchestrator

This root skill coordinates setup, routing, durable state, user gates, and functional workflow
transitions. It does not execute investigation, design, implementation, testing, or validation
itself. Invoke only the installed skill for the current workflow block.

## 1. Prepare the Runtime

### Install and Verify the Agent Crew

Bundled crew version: `1.0.5`. Compare the `version:` frontmatter of all bundled agents with
project-local and global `.claude/agents/` installs. Missing version is `0`. If any agent is missing
or older, update the complete crew atomically; preserve an equal or newer installed crew.

Required Task `subagent_type` values:

- `code-flow-analyzer`
- `ux-design-reviewer`
- `architecture-reviewer`
- `technical-resource-investigator`
- `investigation-documenter`
- `feature-implementer`
- `test-implementer`
- `feature-validator`

### Install and Verify the Functional Skill Crew

Bundled skill crew version: `1.0.0`. Bundled directories under `skills/`:

- `dev-dude-architecture`
- `dev-dude-feature-design`
- `dev-dude-feature-implementation`
- `dev-dude-validation`

Install them as sibling skills alongside the active root:

- project root at `<repo>/.claude/skills/dev-dude/` → `<repo>/.claude/skills/<skill-name>/`
- user root at `~/.claude/skills/dev-dude/` → `~/.claude/skills/<skill-name>/`

For each installed `SKILL.md`, compare its top-level `version:` with the bundled version. Missing
skill or version is `0`.

- If every installed version equals the bundle, keep the crew.
- If none is newer and any is missing or older, copy all four bundled directories to a staging
  directory under the target, verify every staged name/version, then replace all four installed
  directories only after staging succeeds. Remove staging on failure and leave the installed crew
  unchanged.
- If any installed version is newer while another is missing or older, stop at a version-conflict
  gate rather than mixing versions or silently downgrading.
- If every installed version is equal to or newer than the bundle, preserve the installed crew and
  report newer versions.

Verify all four names are discoverable through the Skill capability before dispatch. If copying or
discovery fails because of permissions, stop at a **FUNCTIONAL SKILL INSTALL GATE**, report the exact
target and failure, and ask the user before trying any alternative location or method.

Confirm `TeamCreate` is available. If not, stop with remediation. Install Mermaid CLI
(`npm install --global @mermaid-js/mermaid-cli`) or require the documenter to report use of an
available parser fallback.

### Build Session Context

1. Detect available code-indexing MCP servers. At least one is required. If several are available,
   ask the user to select; auto-select a sole indexer. Run its onboarding when needed.
2. Build `$INDEXER_CONTEXT` with each selected indexer's prefix, search, symbol, modification, and
   memory capabilities. Load relevant project memories.
3. Separately detect documentation MCP, GitHub/registry lookup, and WebFetch/WebSearch tools. Build
   `$RESOURCE_RESEARCH_CONTEXT` and bind it to
   [trusted-source-policy.md](references/trusted-source-policy.md). If reliable external research is
   unavailable, record that and require repository-local investigation only.

If a critical prerequisite fails, report remediation and stop.

## 2. Route the Command

Normalize arguments in this order:

1. Exactly two tokens ending in `refresh` route to Architecture Delta Refresh; reject multi-token
   refresh scopes.
2. `DudeWhereIsMyArch`, `arch`, or `where` route to Architecture Investigation.
3. `DudeWriteMyFeature`, `feature`, or `write` route to Feature Design & Implementation.
4. Otherwise print usage and stop.

Architecture accepts `all`, an area, a directory, or `<all|vertical> refresh`. Feature accepts text,
`.md`, `.txt`, `.docx`, `.pdf`, image paths, or multiple paths. Derive a lowercase, hyphenated
feature slug of at most 40 characters.

## 3. Recover or Initialize State

Read [orchestration-state.md](references/orchestration-state.md) on every command entry, phase entry,
direct resume, or suspected compaction.

- Architecture state: `./docs/ArchOverview/.dev-dude-run-state.md`
- Feature state: `./docs/<feature-slug>/.dev-dude-run-state.md`

Create state before the first delegated task. If state exists, reconcile it with actual outputs,
task results, repository changes, and gate evidence before choosing a transition. Update it before
and after every task, gate, workflow-block transition, and validation attempt.

## 4. Dispatch Functional Workflows

| Reconciled condition | Load and execute |
|---|---|
| Architecture run is incomplete | Invoke `dev-dude-architecture` at its first incomplete step |
| Feature design is not explicitly approved | Invoke `dev-dude-feature-design` at its first incomplete step |
| Feature design is approved but implementation/test evidence is incomplete | Invoke `dev-dude-feature-implementation` |
| Implementation and paired-test evidence is complete | Invoke `dev-dude-validation` |
| Validation requests production/test remediation | Invoke the named implementation skill, then `dev-dude-validation` |
| Feature clarification changes the design materially | Invoke `dev-dude-feature-design` for renewed approval |
| Workflow exit contract is met | Record final status and report |

At each dispatch:

1. Record the current block, step, and one permitted next transition.
2. Invoke the installed functional skill by name through the Skill capability.
3. Pass relevant durable outputs, state path, current step, global invariants, trusted-source and
   document-template paths when relevant, `$INDEXER_CONTEXT`, and the orchestration envelope.
4. Pass `$RESOURCE_RESEARCH_CONTEXT` only to `dev-dude-feature-design`.
5. Require each skill to return evidence and control to this root orchestrator.
6. Reconcile and checkpoint before invoking the next skill.

## 5. Global Invariants

- Root orchestration owns all phase transitions and gate status.
- Never infer user approval. Pause at every gate until an explicit decision is recorded.
- Maximum concurrent Code-Flow-Analyzers: 6.
- Maximum concurrent Feature-Implementers: 3.
- Every investigation-documenter task that changes files has explicit write permission.
- Every Feature-Implementer result has a corresponding Test-Implementer result before validation.
- Root owns the bounded validation attempt counter and all remediation re-dispatch.
- Feature work finishes only on validator `SATISFIED` or a recorded bounded-unresolved state.
- Discover and run available project build, test, lint, and type-check commands before feature
  completion.
- Remove `.tmp/` artifacts after their consuming block finishes. Preserve normal outputs and
  `.dev-dude-run-state.md`.
- Shut down all team agents and delete the team after the final state is recorded.

## 6. Stable Outputs

Architecture documents remain in `./docs/ArchOverview/`. Feature documents remain in
`./docs/<feature-slug>/` and follow
[doc-format-templates.md](references/doc-format-templates.md). Durable state is additive and does not
replace investigation, design, implementation, or verification documents.
