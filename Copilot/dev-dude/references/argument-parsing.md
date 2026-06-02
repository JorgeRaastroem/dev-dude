# Argument Parsing

Parse `$ARGUMENTS` — the first token determines the command:

| Token | Command |
|-------|---------|
| `DudeWhereIsMyArch`, `arch`, `where` | Architecture Investigation |
| `DudeWriteMyFeature`, `feature`, `write` | Feature Design & Implementation |

Remaining tokens after the command = the argument:
- For `arch`: area name or "all" for full investigation
- For `feature`: feature description text, path to a spec file, or path to images

If no recognized command, print usage:
```
DevDude - Architecture Investigation & Feature Implementation

Usage:
  /dev-dude DudeWhereIsMyArch [area|all]
  /dev-dude DudeWriteMyFeature <description|spec-path|image-paths>

Aliases:
  arch, where  → DudeWhereIsMyArch
  feature, write → DudeWriteMyFeature

Examples:
  /dev-dude arch all                    # Full codebase architecture investigation
  /dev-dude arch authentication         # Deep-dive into auth area
  /dev-dude where src/services/         # Investigate a specific directory
  /dev-dude feature Add user caching    # Implement from a feature description
  /dev-dude write ./specs/my-feature.md # Implement from a spec document
```
