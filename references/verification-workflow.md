# Verification Workflow

Generic process for verifying documentation accuracy against actual code.

Use the code indexer tools provided in `$INDEXER_CONTEXT`. The examples below use Serena tool
names — substitute the equivalent tool from your active indexer(s).

## Verification Steps

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

## Verification Report Format

For each item verified, record:
- **Item**: What was checked (file path, symbol, claim)
- **Status**: Accurate / Inaccurate / Minor correction needed
- **Evidence**: What tool call confirmed/denied it
- **Correction** (if inaccurate): What the document should say instead

## Fix Application Rules

1. **One pass only**: Apply corrections once, do not re-verify after fixing
   - This prevents infinite verification-fix loops
   - Trust the verification report and apply corrections faithfully

2. **Minimal edits**: Only change what the verification report identifies
   - Do not rewrite entire sections
   - Do not add new content during fixes
   - Preserve the document's structure and voice

3. **Annotate uncertainties**: If something can't be verified, add a note:
   ```markdown
   > **Note**: This section could not be fully verified. <reason>
   ```

4. **Preserve accurate content**: Never modify items marked as accurate

## Thresholds

- **Accuracy > 90%**: Document is good, apply minor corrections
- **Accuracy 70-90%**: Document needs significant corrections, investigate root causes
- **Accuracy < 70%**: Document may need to be regenerated from better investigation
