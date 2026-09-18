# Issue #44: Durable Orchestration Implementation Plan

**Date**: 2026-09-17  
**Selected design**: Option 1 — Thin Orchestrator with Durable Run State  
**Scope**: Claude and Copilot DevDude skills

## Goals

1. Keep each root `SKILL.md` responsible only for setup sequencing, command routing, global
   orchestration invariants, recovery, and functional-skill dispatch.
2. Persist enough phase, task, gate, and transition state to recover after compaction.
3. Reconcile persisted state with real workflow outputs before resuming.
4. Preserve existing commands, agents, output documents, gates, concurrency limits, and validation
   behavior in both runtimes.

## Correction to the Prior Implementation

Workflow references are not skills. Option 1 requires separately discoverable and invocable skill
packages with their own `SKILL.md`, ownership boundary, and version. The root must invoke those
installed skills rather than read workflow references as if they were skills.

## Bundled Functional Skills

| Skill | Responsibility | Exit |
|---|---|---|
| `dev-dude-architecture` | Discovery, investigation, documentation, vertical gate, verification, review, and fixes | Verified architecture documents |
| `dev-dude-feature-design` | Feature investigation, resource research, options, critique, and selection gate | Explicitly approved design |
| `dev-dude-feature-implementation` | Clarification gate, plan, production changes, and paired tests | Implementation and test evidence |
| `dev-dude-validation` | One validation attempt: project checks, semantic verification, validator decision, and remediation route | `SATISFIED`, targeted route, or bounded unresolved |

Each runtime bundle contains all four sibling skill directories under `skills/`. Every skill has
`name`, `description`, and a shared `version` in frontmatter. Detailed material may remain in that
skill's own `references/` directory, but not in the root skill's workflow references.

## Auto-Install and Upgrade

1. The root checks the four bundled skill versions before workflow dispatch.
2. Claude installs alongside the active root scope: `.claude/skills/` for a project root or
   `~/.claude/skills/` for a user root.
3. Copilot installs user-wide under `~/.copilot/skills/`.
4. Missing version is `0`. If any installed skill is missing or older, copy the complete bundled
   skill crew atomically so its versions cannot drift.
5. Preserve a complete installed crew when every installed version is equal to or newer than the
   bundle. Never silently downgrade a newer skill.
6. Verify all four installed names are discoverable through the runtime's Skill capability before
   routing. Stop with remediation if installation or discovery fails.

## Root Orchestrator Changes

1. Keep the runtime-neutral durable state contract and orchestration envelope.
2. Keep setup, argument routing, state reconciliation, gates, and transitions in root.
3. Replace workflow-reference dispatch with explicit installed-skill invocation.
4. Pass the run-state path, current step, approved inputs, context inventories, global invariants,
   and expected exit evidence to the selected skill.
5. Require the skill to return control to root. Root reconciles and selects the next skill.
6. Root owns the bounded attempt counter and remediation re-dispatch; validation owns each attempt's
   evidence, decision, and route.

## Compatibility

- Architecture outputs remain under `./docs/ArchOverview/`.
- Feature outputs remain under `./docs/<feature-slug>/`.
- Active state is stored beside those outputs as `.dev-dude-run-state.md`.
- State files persist after successful runs as an audit and resume record; only `.tmp/` artifacts
  are removed.
- Claude and Copilot use the same states and transitions. Runtime-specific agent and tool syntax
  remains inside their corresponding bundled skills.

## Validation

- Verify all eight bundled `SKILL.md` files have valid names matching their directories and one
  shared version.
- Verify both roots install and invoke all four functional skills from valid runtime discovery
  directories.
- Verify feature design does not implement code, feature implementation does not own final
  validation, and validation owns the bounded loop.
- Verify state contracts define the same required fields, reconciliation order, and task envelope.
- Verify bundled-skill parity after normalizing runtime-specific agent names/tool syntax.
- Check bundled local links, whitespace, and changed-file scope.
