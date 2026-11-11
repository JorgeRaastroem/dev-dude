# Verification Workflow

Nonnormative examples only. The normative workflow is `workflow.yaml` (root copy
`skills/dev-dude-validation/references/workflow.yaml`, manifest load set `stage.dev-dude-validation`). Examples show call shapes;
where they differ from YAML rules (for example model selection, concurrency, or write ownership),
the YAML rules win.

## Example: Validator Gate

```markdown
# Feature Verification Report

## Verification Status
SATISFIED | UNSATISFIED

## Summary
<concise result>

## Evidence Reviewed
- Original spec/design:
- Implementation summaries:
- Test summaries/results:
- Project commands:
- Code-flow findings:
- Changed files:

## Criteria Results
| Criterion | Status | Evidence |
|-----------|--------|----------|

## Failed Criteria
<None, or each failed criterion with evidence>

## Required Remediation Tasks
| Task | Owner Agent | Input Evidence | Expected Output |
|------|-------------|----------------|-----------------|

## Unresolved Questions
<None, or user clarification needed>
```

## Example: Documentation Fix Application Rules

```markdown
> **Note**: This section could not be fully verified. <reason>
```
