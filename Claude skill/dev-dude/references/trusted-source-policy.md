# Trusted Source Policy

Shared policy reference for technical resource investigation. It governs **which sources may be
cited** when recommending external packages, services, platforms, or other resources, and how
factual claims must be grounded.

This policy is **behavioral / source-quality enforcement**, not domain-restricted tool gating. In
Claude/Copilot agents, web and research tools cannot be technically locked to specific domains —
source restriction is a prompt/behavioral policy. The single enforceable rule is the **citation-host
invariant**: every external recommendation must carry an allowlisted, authoritative citation, and
any external factual claim must be traceable to an allowlisted source. Recommendations that cannot
satisfy the citation-host invariant must not be made.

## Citation-Host Invariant (Enforceable Rule)

1. Every recommended external resource **must** include at least one citation whose host is on the
   allowlist below (or a documentation MCP document reference).
2. Every external **factual** claim (versions, license, maintenance status, advisories, capabilities)
   **must** be traceable to an allowlisted source via an explicit URL or MCP document reference.
3. **Facts and recommendations are separated.** Recommendations are the agent's judgment; facts are
   cited evidence. A recommendation may not silently smuggle in an uncited factual assertion.
4. A candidate that cannot satisfy this invariant **cannot be recommended** — record it as
   `unverified` instead.

## Allowlisted Authoritative Sources

- **Documentation MCP servers** available in the session (e.g., a docs/context MCP server). Cite as
  an MCP document reference.
- **Official vendor / framework documentation** sites (the project's own canonical docs domain).
- **GitHub** repository, release, and **Security Advisory** (GHSA) pages
  (`github.com/<org>/<repo>`, `github.com/.../releases`, `github.com/advisories`).
- **Official package registries** — e.g., `npmjs.com`, `pypi.org`, `crates.io`, `pkg.go.dev`,
  `nuget.org`, `rubygems.org`, Maven Central.
- **Official package documentation** linked directly from the registry page or the project's GitHub
  repository.
- **OSV** (`osv.dev`) and **GitHub Security Advisories** for vulnerability / advisory lookups.

## Prohibited Sources

Do **not** cite or rely on:

- Random blogs, personal websites, or Medium/Dev.to-style opinion posts.
- SEO "best X libraries" / comparison / listicle pages.
- Stack Overflow / forum answer snippets as authoritative facts.
- Uncited, model-generated lists or summaries presented as fact.
- Arbitrary search-result summaries not backed by an allowlisted page.

These may occasionally surface a lead, but a lead is not a citation. Any candidate they surface must
be re-verified against an allowlisted source before it can be cited or recommended.

## Advisory Lookup Preferences

Prefer **read-only advisory sources** that do not require an installed dependency tree:

- **GitHub Security Advisories** (`github.com/advisories`, GHSA identifiers).
- **OSV** (`osv.dev`).

Do **not** rely on tools that assume an installed dependency tree (e.g., `npm audit`,
`pip-audit` against a local environment). Investigation is read-only and must not install,
fetch-and-execute, or build third-party code.

## Graceful Degradation (Unavailable Research Tools)

When reliable research tooling is unavailable, **do not substitute low-quality sources**:

- If no documentation MCP server and no reliable web/registry lookup is available, mark external
  research as **unavailable** and fall back to **repository-local discovery and validation only**.
- Record every unavailable source and research gap explicitly in the investigation document rather
  than filling the gap with prohibited sources.
- An external candidate that cannot be verified through an allowlisted source remains `unverified`
  and cannot be recommended, regardless of how promising it appears.
