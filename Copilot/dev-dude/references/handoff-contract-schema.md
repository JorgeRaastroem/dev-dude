# Handoff Contract Schema

Every stage boundary uses a YAML contract. Preserve identifiers across contracts when referring to
the same item; allocate a new identifier when meaning changes. Empty typed lists are explicit (`[]`).

```yaml
handoff:
  schema_version: "1.0"
  workflow_id: "<architecture|feature>"
  workflow_version: "<workflow definition or amendment version>"
  run_id: "<stable run identifier>"
  contract_id: "<stable unique contract identifier>"
  producing_stage: "<stage name or root-initialization>"
  receiving_stage: "<next stage name or null for terminal>"
  status: "complete | partial | blocked | failed"

objective:
  statement: "<bounded objective attempted by the producing stage>"
  completion_criteria:
    - id: "CC001"
      statement: "<measurable criterion>"
      status: "met | unmet | not_applicable"
      evidence: ["ART001#<specific locator>"]

verified_facts:
  - id: "F001"
    statement: "<fact>"
    evidence:
      - artifact_id: "ART001"
        locator: "<file:line, document section, query, or durable result reference>"
    verification_status: "verified"

assumptions:
  - id: "A001"
    statement: "<provisional claim>"
    reason: "<why it is needed>"
    verification_status: "unverified | partially_verified"
    impact_if_false: "<impact>"

constraints:
  - id: "C001"
    statement: "<rule or limitation>"
    source: "<workflow, policy, contract item, or ART001#locator>"

decisions:
  - id: "D001"
    statement: "<selected course>"
    rationale: "<concise, outcome-relevant rationale>"
    based_on: ["F001", "C001"]

rejected_approaches:
  - id: "R001"
    approach: "<excluded option>"
    reason: "<evidence-based reason>"
    based_on: ["F001"]

artifacts:
  - id: "ART001"
    uri_or_path: "<durable path or URI>"
    media_type: "<media type>"
    digest: "<optional algorithm:value>"
    purpose: "<downstream need>"
    access: "required | optional"

open_questions:
  - id: "Q001"
    question: "<unresolved information>"
    owner_stage: "<responsible stage>"
    blocking: true

blockers:
  - id: "B001"
    description: "<condition preventing safe progression>"
    required_resolution: "<specific action or evidence>"

failures:
  - id: "X001"
    dependency: "<tool or artifact>"
    category: "<error category>"
    action_attempted: "<action>"
    retry_or_escalation: "<safe condition>"

continuation:
  remaining_criteria: ["CC001"]
  next_action: "<precise restart point or null>"

next_stage:
  objective: "<bounded next objective or null for terminal>"
  required_inputs: ["F001", "ART001"]
  authorized_artifacts: ["ART001"]
  authorized_tools: ["<tool or capability>"]
  prohibited_dependencies:
    - "prior conversation history"
    - "unreferenced artifacts"
    - "unverified assumptions treated as facts"

validation:
  result: "pending | pass | fail"
  validated_by: "<root stage/gate identifier>"
  issues:
    - code: "<stable issue code>"
      location: "<field path>"
      message: "<failure>"
      remediation: "<specific corrective action>"
```

## Required Semantics

- All top-level sections are required. Use empty lists or `null` where the schema permits. A
  producing stage sets `validation.result: pending`; only the root gate changes it to `pass` or
  `fail`. A receiving stage accepts only `pass`.
- Nonterminal contracts require `receiving_stage`, a bounded `next_stage.objective`, and authorized
  tools/artifacts. Terminal contracts set those values to `null` or empty lists.
- `complete` requires every applicable completion criterion to be `met`, no blocking open question,
  no blocker, and no unresolved failure.
- `partial` requires unmet criteria and a precise `continuation`; `blocked` requires a blocker or
  blocking question; `failed` requires a recorded failure. None authorizes a different next stage.
- Every verified fact requires resolvable evidence. Confidence wording is not evidence.
- Assumptions remain assumptions until new evidence supports a separately recorded verified fact.
- Decisions and rejections reference declared facts or constraints in `based_on`.
- Artifact authorization is least-access: listing an artifact permits access only for its stated
  purpose. A present digest must match before use.
- Record contradictions as blocking open questions with both claims and evidence references until an
  allowed resolution stage resolves them.
- Never serialize chain-of-thought, raw scratchpads, tool chatter, or whole transcripts.

The root creates the initial contract from normalized command input and verified runtime state. A
stage writes all sections with a pending validation outcome; the root gate records the final outcome
after independent validation.
