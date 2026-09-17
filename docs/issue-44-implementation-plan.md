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

## Changes

1. Add a runtime-neutral `orchestration-state.md` contract to both reference sets.
2. Keep architecture investigation in `arch-investigation-workflow.md`.
3. Limit `feature-design-workflow.md` to investigation through the user review gate.
4. Move clarification, planning, implementation, testing, and bounded validation into a new
   `feature-implementation-workflow.md`.
5. Replace duplicated workflow summaries in each root skill with dispatch rules and a compact
   orchestration envelope.
6. Update the README structure and explain durable recovery behavior.

## Compatibility

- Architecture outputs remain under `./docs/ArchOverview/`.
- Feature outputs remain under `./docs/<feature-slug>/`.
- Active state is stored beside those outputs as `.dev-dude-run-state.md`.
- State files persist after successful runs as an audit and resume record; only `.tmp/` artifacts
  are removed.
- Claude and Copilot use the same states and transitions. Runtime-specific agent and tool syntax
  remains in their functional workflow files.

## Validation

- Verify both root skills reference every required functional workflow.
- Verify feature design files no longer contain implementation execution steps.
- Verify feature implementation files retain clarification, testing, validation, and remediation
  contracts.
- Verify state contracts define the same required fields, reconciliation order, and task envelope.
- Check all local Markdown links, paired reference headings, whitespace, and changed-file scope.
