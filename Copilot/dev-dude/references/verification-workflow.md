# Verification Workflow

Generic process for verifying documentation accuracy and feature implementation accuracy against actual code.

Use the code indexer tools provided in `$INDEXER_CONTEXT`. The examples below use Serena tool names; substitute the equivalent tool from your active indexer(s).

## Documentation Verification Steps

### 1. File Path Verification

For every file path mentioned in the document:
- Use the indexer's `find_file` / `list_dir` capability (e.g., `mcp__serena__find_file("<filename>", "<directory>")` or `mcp__serena__list_dir("<path>", recursive=false)`)
- Mark as accurate if file exists at the stated path
- Mark as inaccurate if file doesn't exist; search for the correct path

### 2. Symbol Verification

For every class, function, interface, or type mentioned:
- Use the indexer's `find_symbol` capability (e.g., `mcp__serena__find_symbol("<name>", relative_path="<stated-path>")` with `include_body=false`)
- Mark as accurate if symbol exists in the stated location
- Mark as inaccurate if symbol doesn't exist or is in a different location

### 3. Code Snippet Verification

For code snippets or specific implementation claims:
- Use the indexer's `find_symbol` with body inclusion (e.g., `mcp__serena__find_symbol("<name>", relative_path="<path>", include_body=true)`)
- Compare the actual body with what's described in the document
- Mark as accurate if description matches implementation
- Mark as inaccurate if there are meaningful differences

### 4. Dependency Verification

For claims about dependencies and relationships:
- Use the indexer's `find_referencing_symbols` capability (e.g., `mcp__serena__find_referencing_symbols("<name>", relative_path="<path>")`)
- Verify that stated consumers/dependents actually reference the symbol
- Check for missing relationships not mentioned in the document

### 5. Architecture Claim Verification

For higher-level architecture claims (patterns, conventions, data flow):
- Use the indexer's `search_for_pattern` capability (e.g., `mcp__serena__search_for_pattern("<pattern>")`) to find evidence
- Verify at least 2-3 concrete examples support the claim
- Mark as inaccurate if no evidence found or evidence contradicts

## Feature Implementation Verification

Feature implementation verification is a completion gate for Phase 2 of `DudeWriteMyFeature`. It is not optional and must run whether Phase 2 follows Phase 1 or resumes directly from an existing design/implementation plan.

### Required Inputs

- Original feature spec or user request
- Approved design option and design document
- Implementation plan and current Phase 2 state
- Implementation summaries from all Feature-Implementer tasks
- Test summaries/results from all Test-Implementer tasks
- Changed files
- Project validation command results
- Code-Flow-Analyzer semantic verification findings when flow/integration behavior is non-trivial
- Current remediation attempt number and max attempts

### Verification Criteria

| Criterion | Requirement |
|-----------|-------------|
| Implementation plan complete | Every planned task has a completed implementation summary or an explicit reason it is not needed |
| Tests paired with implementation | Every Feature-Implementer result has a corresponding Test-Implementer result |
| Project validation run | Build/test/lint/type-check commands are run when available, with unavailable commands explicitly reported |
| Spec/design satisfied | Implemented behavior matches the original spec and approved design |
| Integration verified | Affected code flows and integration points are verified against actual code |
| Evidence sufficient | Changed files, command results, and summaries are current for the latest remediation attempt |

### Validator Gate

Use the Feature-Validator agent as the final read-only gate. Code-Flow-Analyzer can provide semantic flow evidence, but Feature-Validator owns the final `SATISFIED` or `UNSATISFIED` decision.

Feature-Validator must write or update `./docs/<feature-slug>/verification.md` using this result shape:

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

### Remediation Loop Rules

1. **Bounded loop**: Default to 3 validation attempts unless the user explicitly sets a different limit.
2. **Correct owner routing**:
   - Production code gap, incomplete behavior, or spec mismatch: Feature-Implementer
   - Missing, incorrect, or brittle tests: Test-Implementer
   - Unclear flow behavior or insufficient semantic evidence: Code-Flow-Analyzer, then Feature-Validator rerun
   - Ambiguous or conflicting requirement: user clarification gate
3. **Full loop after remediation**: Production-code remediation must be followed by Test-Implementer before validation reruns.
4. **Current evidence only**: Do not reuse stale command results or stale verification reports after files change.
5. **Exit conditions**: Phase 2 exits only on `SATISFIED`, or on a bounded unresolved state that lists failed criteria, evidence, owner agents, and remaining questions.

## Documentation Verification Report Format

For each item verified, record:
- **Item**: What was checked (file path, symbol, claim)
- **Status**: Accurate / Inaccurate / Minor correction needed
- **Evidence**: What tool call confirmed/denied it
- **Correction** (if inaccurate): What the document should say instead

## Documentation Fix Application Rules

1. **One pass only for documentation fixes**: Apply documentation corrections once, do not re-verify after fixing.
   - This prevents documentation-only verification-fix loops.
   - This rule does not apply to Phase 2 feature implementation verification, which uses the bounded remediation loop above.

2. **Minimal edits**: Only change what the verification report identifies.
   - Do not rewrite entire sections.
   - Do not add new content during fixes.
   - Preserve the document's structure and voice.

3. **Annotate uncertainties**: If something can't be verified, add a note:
   ```markdown
   > **Note**: This section could not be fully verified. <reason>
   ```

4. **Preserve accurate content**: Never modify items marked as accurate.

## Documentation Accuracy Thresholds

- **Accuracy > 90%**: Document is good, apply minor corrections
- **Accuracy 70-90%**: Document needs significant corrections, investigate root causes
- **Accuracy < 70%**: Document may need to be regenerated from better investigation