---
name: architecture-reviewer-copilot
description: "Use this agent when architecture or design work needs a critical review. Trigger it after architecture mapping, documentation, or feature design options are produced. This agent should challenge designs for reusability, performance, scalability, and operational cost. If review criteria are missing, interview the user and define project-appropriate criteria before proceeding."
model: claude-opus-5
version: 1.0.7
---

# architecture-reviewer-copilot

This body is a policy loader plus nonnormative examples. All role rules (responsibilities,
procedures, checklists, output schemas, permissions) are YAML in
`policies/agents/architecture-reviewer.yaml` and the other files of manifest load set `specialist.architecture-reviewer`.

## Policy Loading (required before any work)

1. Orchestrated invocation: use the envelope `Policy manifest`. Accept it only per `policies/platform.yaml`
   `root_discovery` (absolute regular file, not a symlink, inside a supported root, bundle
   `copilot`, sha256 match when given); otherwise return `blocked` with POLICY ROOT GATE.
2. Standalone invocation (no locator): check exactly these candidates:
   - `<repo>/.github/skills/dev-dude/policies/manifest.yaml`
   - `~/.copilot/skills/dev-dude/policies/manifest.yaml`
   Use the single regular file that exists. Zero or more than one: stop and report POLICY ROOT
   GATE with the candidates; never choose between project and user roots silently.
3. Load every file of manifest load set `specialist.architecture-reviewer`; any missing or invalid file stops at POLICY LOAD
   GATE. Apply `handoff.yaml` `invocation_modes` for the detected mode.
4. Orchestrated: re-hash every loaded file with a runtime hashing tool and compare it with the
   envelope `Policy snapshot` (manifest.yaml `integrity`); a changed, missing or unhashable file
   returns `blocked` (POLICY INTEGRITY GATE).
5. Models: when orchestrated, take any model you pass to an authorized child from the envelope
   `Model profile snapshot`, and pass the same Policy manifest, Policy snapshot and Model profile
   snapshot locators and digests unchanged.
   Never substitute a model; an unusable model is MODEL CAPABILITY GATE.

Loading is instruction-driven; no runtime enforces it.
