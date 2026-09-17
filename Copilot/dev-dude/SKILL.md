---
name: dev-dude
description: >
  Resumable architecture investigation and feature implementation using agent fleets.
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
itself. Load only the reference for the current workflow block.

## 1. Prepare the Runtime

### Install and Verify the Agent Crew

Bundled crew version: `1.0.5`. Compare the `version:` frontmatter of all bundled agents with
`~/.copilot/agents/`. Missing version is `0`. If any agent is missing or older, update the complete
crew atomically; preserve an equal or newer installed crew.

Required custom agent types:

- `code-flow-analyzer-copilot`
- `ux-design-reviewer-copilot`
- `architecture-reviewer-copilot`
- `technical-resource-investigator-copilot`
- `investigation-documenter-copilot`
- `feature-implementer-copilot`
- `test-implementer-copilot`
- `feature-validator-copilot`

Every `task` call must pass the selected agent's reasoning-agnostic frontmatter `model` alias.
Install Mermaid CLI (`npm install --global @mermaid-js/mermaid-cli`) or require the documenter to
report use of an available parser fallback.

### Build Session Context

1. Detect available code-indexing MCP servers. If several are available, ask the user to select;
   auto-select a sole indexer and run onboarding when needed. If none is available, inform the user
   and use standard `grep`, `glob`, and `view` tools.
2. Build `$INDEXER_CONTEXT` with selected indexer capabilities, or the standard-tool fallback. Load
   relevant project memories where supported.
3. Separately detect documentation MCP, GitHub/registry lookup, and WebFetch/WebSearch tools. Build
   `$RESOURCE_RESEARCH_CONTEXT` and bind it to
   [trusted-source-policy.md](references/trusted-source-policy.md). If reliable external research is
   unavailable, record that and require repository-local investigation only.

If a critical prerequisite fails, report remediation and stop.

## 2. Route the Command

Parse arguments using [argument-parsing.md](references/argument-parsing.md):

- `<all|vertical> refresh` routes to Architecture Delta Refresh.
- `DudeWhereIsMyArch`, `arch`, or `where` route to Architecture Investigation.
- `DudeWriteMyFeature`, `feature`, or `write` route to Feature Design & Implementation.

Derive a lowercase, hyphenated feature slug of at most 40 characters for feature state and outputs.
Feature input may be text, `.md`, `.txt`, `.docx`, `.pdf`, image paths, or multiple paths.

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
| Architecture run is incomplete | [arch-investigation-workflow.md](references/arch-investigation-workflow.md), first incomplete step |
| Feature design is not explicitly approved | [feature-design-workflow.md](references/feature-design-workflow.md), first incomplete step |
| Feature design is approved | [feature-implementation-workflow.md](references/feature-implementation-workflow.md), first incomplete step |
| Feature clarification changes the design materially | Return to feature design and renewed approval |
| Workflow exit contract is met | Record final status and report |

At each dispatch:

1. Record the current block, step, and one permitted next transition.
2. Load only that functional reference and relevant durable outputs.
3. Add the orchestration envelope from `orchestration-state.md` and `$INDEXER_CONTEXT` to every
   delegated task. Add `$RESOURCE_RESEARCH_CONTEXT` only where the functional workflow requires it.
4. Pass the agent's frontmatter `model` alias and use background mode only for independent work.
5. Require each block to return evidence and control to this root orchestrator.
6. Reconcile and checkpoint before dispatching the next block.

## 5. Global Invariants

- Root orchestration owns all phase transitions and gate status.
- Never infer user approval. Pause at every gate until an explicit decision is recorded.
- Maximum concurrent Code-Flow-Analyzers: 6.
- Maximum concurrent Feature-Implementers: 3.
- Every investigation-documenter task that changes files has explicit write permission.
- Every Feature-Implementer result has a corresponding Test-Implementer result before validation.
- Feature work finishes only on validator `SATISFIED` or a recorded bounded-unresolved state.
- Discover and run available project build, test, lint, and type-check commands before feature
  completion.
- Remove `.tmp/` artifacts after their consuming block finishes. Preserve normal outputs and
  `.dev-dude-run-state.md`.

## 6. Stable Outputs

Architecture documents remain in `./docs/ArchOverview/`. Feature documents remain in
`./docs/<feature-slug>/` and follow
[doc-format-templates.md](references/doc-format-templates.md). Durable state is additive and does not
replace investigation, design, implementation, or verification documents.
