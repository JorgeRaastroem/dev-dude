---
name: dev-dude
version: 1.1.0
description: >
  Resumable architecture investigation and feature implementation using agent swarms.
  DudeWhereIsMyArch (arch/where) writes architecture docs to ./docs/ArchOverview/.
  DudeWriteMyFeature (feature/write) accepts descriptions, specs, or images and writes design,
  implementation, and verification outputs to ./docs/<feature-slug>/.
  update fetches the latest DevDude bundle and reloads supported runtimes.
---
argument-hint:
  - "update" — Update DevDude and reload its skills and agents
  - "models show" — Show the resolved model profile and its sources
  - "models profiles" — List profiles per scope and which is active
  - "models validate" — Validate model configuration files offline
  - "models set <role|all> <model-id> --profile <name> --scope <project|user>" — Save an unvalidated draft profile entry
  - "models use <profile|bundled-default> --scope <project|user>" — Select the active model profile
  - "models reset --scope <project|user>" — Remove this runtime's model configuration in a scope
  - "DudeWhereIsMyArch all" — Full architecture investigation
  - "all refresh" — Refresh affected architecture docs
  - "authentication refresh" — Refresh one architecture vertical
  - "DudeWhereIsMyArch authentication" — Investigate one area
  - "DudeWriteMyFeature Add user caching" — Design and implement a feature

# DevDude Root Orchestrator

Bundled agent crew version: `1.0.8`.
Bundled skill crew version: `1.1.4`.

DevDude policy is YAML. This file is only the host/controller loader and the ordered step index;
it does not restate policy values. Each step names the policy IDs to apply. Resolve an ID through
`policies/manifest.yaml` `policy_index`, then apply its `rules`, `resolutions`, `defaults` and
`exceptions` with the precedence in `manifest.yaml` `loading.precedence`. Loading is
instruction-driven: nothing in the runtime enforces it, so follow every load step explicitly.

Both version sentences are read by the update check and equal `policies/metadata.yaml` `crews`
(META-CREW-001, META-CREW-002). Only the agent crew sentence is rewritten by
`.github/workflows/bump-agent-versions.yml` (`metadata.yaml` `version_bump`); the skill crew and root
versions are bumped manually.

## 0. Policy Root and Loading

1. The candidate root is the directory containing this SKILL.md. Load `policies/platform.yaml` and
   apply `root_discovery`; refuse a source checkout for launch. Stop at POLICY ROOT GATE on zero,
   ambiguous, symlinked, or bundle-mismatched roots.
2. Load `policies/manifest.yaml`; check `bundle: claude`. Load the load set named for the current entry
   (below) per `manifest.yaml` `loading.rules`. Any load failure stops at POLICY LOAD GATE.
3. Record the absolute manifest path and hash every policy file with a runtime hashing tool per
   `manifest.yaml` `integrity` (never estimate a hash; no tool -> POLICY INTEGRITY GATE). The
   manifest digest and the policy snapshot (bundle revision + per-file sha256) become the
   `policy_context` passed to the controller and to every stage and specialist (BOOT-PKT-001.R08/R13,
   ENV-001.R07, HOC-SCHEMA-001.R16).

## 1. Host Steps

These steps are host-only (META-ROOT-003, UPD-CHECK-001.R01). A controller receiving
`entry_role: orchestrator` skips to section 2.

### 1.1 Parse the Command

Apply CMD-ROUTE-001, CMD-INPUT-001 and CMD-USAGE-001 from `policies/commands.yaml`. Print
`commands.yaml` `usage_text` (or `models_commands.usage_text`) exactly when routing says so.

### 1.2 `models ...` (load set `host.models`)

Apply `commands.yaml` `models_commands` with `policies/models.yaml` (`config`, `syntax`,
`resolution`, `bundled_default`). Offline only: no update check, network, crew install, onboarding,
state, or dispatch (`update.yaml` `launch_check.exceptions`). Report results, then stop.

### 1.3 `update` (load set `host.update`)

Apply UPD-CMD-001 rules R01-R09 in order (pin target, locate the active root and scope, quiescence,
staged download and validation, marker, backup/replace/rollback, reload or UPDATE RELOAD GATE) using
UPD-CHECK-001 for target resolution, `update.yaml` `owned_files`, `platform.yaml`
`root_locations`, INST-AGT-001 and INST-SKL-001 for crew scope. Then stop.

### 1.4 Launch (load set `host.launch`)

Run in order; each gate stops the launch with the remediation its rule gives.

1. Update check: UPD-CHECK-001 (skipped for `update` and `models`).
2. Agent crew: INST-LOCK-001, META-CREW-001, INST-AGT-001 (compare against
   `metadata.yaml` `crews.agents`).
3. Functional skill crew: META-CREW-002, INST-SKL-001, META-SKL-001/FSK-META-001.
4. Runtime prerequisites: INST-RT-001 and `platform.yaml` `capabilities`.
5. Contexts: CTX-IDX-001 (`$INDEXER_CONTEXT`) and CTX-RES-001 (`$RESOURCE_RESEARCH_CONTEXT`,
   bound to TSP-* in `policies/trusted-sources.yaml`, part of load set `host.launch`).
6. Models: resolve the profile with `models.yaml` `resolution`, then run `launch_validation`
   against the delegation tool actually exposed in this session (Task tool with `subagent_type`). Custom profiles that
   cannot be verified stop at MODEL CAPABILITY GATE; bundled-default follows the legacy path.
7. Controller capability and duplicates: BOOT-CAP-001, BOOT-DUP-001 with STATE-LOC-001 and
   WD-* (`policies/watchdog.yaml`).
8. Bootstrap: BOOT-PKT-001 (including `policy_context`, `policy_manifest`, `model_profile`), then
   relay per BOOT-RELAY-001.

## 2. Controller Steps (load set `controller`)

Run only in the dedicated `dev-dude-orchestrator` controller (ORCH-ENTRY-001).

1. Entry: ORCH-ENTRY-001; validate the bootstrap packet, its `policy_context` against this root,
   and the model profile; re-hash every policy file and write the policy snapshot (`manifest.yaml`
   `integrity`), then the pinned model snapshot (`models.yaml` `pinning`). On every resume re-hash
   all policy files and verify both snapshots against run state before anything else; any change
   blocks (POLICY INTEGRITY GATE / MODEL PIN GATE) unless an approved migration is recorded.
2. Parse and route: CMD-ROUTE-001 (an `update` or `models` command reaching the controller returns
   `blocked`).
3. State: ORCH-STATE-001, STATE-* (`policies/state.yaml`), STG-* (`policies/stage-workflow.yaml`).
4. Dispatch: DISP-TABLE-001 and DISP-STEP-001 with ENV-001/HOC-* (`policies/handoff.yaml`),
   VAL-* (`policies/validation-rules.yaml`), FSK-CONTRACT-001, and the target stage
   `skills/<skill>/references/workflow.yaml`.
5. Watchdog: DISP-WD-001 and WD-*.
6. Invariants and outputs: INV-GLOBAL-001, OUT-STABLE-001, TPL-* (`policies/output-templates.yaml`;
   template bodies in `references/doc-format-templates.md`).
7. Role rules for the controller agent: `policies/agents/dev-dude-orchestrator.yaml`.
