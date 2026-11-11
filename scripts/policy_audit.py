#!/usr/bin/env python3
"""Read-only audit of the DevDude Markdown -> YAML policy migration.

Checks repository consistency only:
- every baseline policy and rule in policy-migration-inventory.yaml exists in the correct bundle
  YAML file with the same content (after platform projection), except amendments and additions
  declared in the inventory migration_record;
- manifest index, load sets, actor bindings and consumer loader stubs;
- frontmatter equality with metadata/models YAML and the version-bump workflow regexes;
- deleted Markdown references;
- pure-helper scenarios for the models config/command design (no network, no files written).

It does not execute any host runtime and is not proof that a host loads or obeys the policies.
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit("policy audit requires PyYAML; nothing was checked")

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "policy-migration-inventory.yaml"
WORKFLOW = ROOT / ".github/workflows/bump-agent-versions.yml"
README = ROOT / "README.md"
BUNDLES = {"claude": ROOT / "Claude skill/dev-dude", "copilot": ROOT / "Copilot/dev-dude"}
BUNDLE_PREFIX = {"claude": "Claude skill/dev-dude/", "copilot": "Copilot/dev-dude/"}
SUFFIX = {"claude": "", "copilot": "-copilot"}
ROLE_CODES = {
    "ORC": "dev-dude-orchestrator", "AR": "architecture-reviewer", "UX": "ux-design-reviewer",
    "CFA": "code-flow-analyzer", "TRI": "technical-resource-investigator", "FI": "feature-implementer",
    "TI": "test-implementer", "FV": "feature-validator", "ID": "investigation-documenter",
}
SKILLS = ["dev-dude-architecture", "dev-dude-feature-design", "dev-dude-feature-implementation",
          "dev-dude-validation"]
DELETED = ["orchestration-state.md", "stage-workflow.md", "handoff-contract-schema.md",
           "validation-rules.md", "trusted-source-policy.md", "argument-parsing.md", "policy-index.yaml"]
PLATFORMS = {"claude", "copilot"}
NON_CONTENT = {"amendment", "resolution", "frontmatter_exact", "added_by", "platform", "order"}
POLICY_KEYS = {"title", "kind", "scope", "defaults", "exceptions", "platform_binding", "amendment",
               "rules", "resolutions", "planned_changes", "retained_prose", "source_nuance"}
MARKER_RE = re.compile(r"\n# =+ migration record")

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


# --------------------------------------------------------------------------- strict YAML
class _UniqueLoader(yaml.SafeLoader):
    pass


def _mapping(loader, node, deep=False):
    out = {}
    for k_node, v_node in node.value:
        key = loader.construct_object(k_node, deep=deep)
        if key in out:
            raise ValueError(f"duplicate key {key!r} at line {k_node.start_mark.line + 1}")
        out[key] = loader.construct_object(v_node, deep=deep)
    return out


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def strict_load(text: str):
    """One document; no anchors/aliases, explicit tags, or duplicate keys."""
    try:
        events = list(yaml.parse(text, Loader=yaml.SafeLoader))
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error: {exc}") from None
    if sum(isinstance(e, yaml.DocumentStartEvent) for e in events) != 1:
        raise ValueError("expected exactly one YAML document")
    for e in events:
        if isinstance(e, yaml.AliasEvent) or getattr(e, "anchor", None):
            raise ValueError("anchors/aliases are not allowed")
        if getattr(e, "tag", None) is not None:
            implicit = e.implicit
            explicit = implicit == (False, False) if isinstance(e, yaml.ScalarEvent) else not implicit
            if explicit:
                raise ValueError(f"explicit tag {e.tag} is not allowed")
    try:
        return yaml.load(text, Loader=_UniqueLoader)
    except (yaml.YAMLError, ValueError) as exc:
        raise ValueError(str(exc)) from None


def load_file(path: Path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or non-regular file: {path.relative_to(ROOT)}")
    return strict_load(path.read_text(encoding="utf-8"))


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.relative_to(ROOT)}: missing frontmatter")
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end + 1]), text[end + 5:]


# --------------------------------------------------------------------------- projection
def project_rule(rule: dict, bundle: str):
    if rule.get("platform") and rule["platform"] != bundle:
        return None
    out = {}
    for key, value in rule.items():
        if key == "id":
            continue
        m = re.fullmatch(r"(.+)_(claude|copilot)", key)
        if m:
            if m.group(2) == bundle:
                out[m.group(1)] = copy.deepcopy(value)
            continue
        if isinstance(value, dict) and value and set(value) <= PLATFORMS:
            if bundle in value:
                out[key] = copy.deepcopy(value[bundle])
            continue
        out[key] = copy.deepcopy(value)
    return out


def project_value(value, bundle: str):
    if isinstance(value, dict) and value and set(value) <= PLATFORMS:
        return copy.deepcopy(value.get(bundle))
    if isinstance(value, dict):
        return {k: project_value(v, bundle) for k, v in value.items()}
    return copy.deepcopy(value)


def strip_fences(text: str) -> str:
    return re.sub(r"^(`{3,}|~{3,}).*?^\1\s*$", "", text, flags=re.M | re.S)


def nonempty(value) -> bool:
    return value not in (None, "", [], {})


def get_path(data, dotted: str):
    for part in dotted.split("."):
        if not isinstance(data, dict) or part not in data:
            raise KeyError(dotted)
        data = data[part]
    return data


# --------------------------------------------------------------------------- inventory
def load_inventory():
    text = INVENTORY.read_text(encoding="utf-8")
    m = MARKER_RE.search(text)
    idx = m.start() if m else -1
    if idx < 0:
        raise SystemExit("inventory has no migration_record section")
    baseline_text = text[:idx]
    baseline = yaml.load(baseline_text, Loader=_UniqueLoader)
    full = yaml.load(text, Loader=_UniqueLoader)
    record = full.get("migration_record")
    if not isinstance(record, dict):
        raise SystemExit("migration_record missing")
    for key in baseline:
        if full[key] != baseline[key]:
            fail(f"inventory baseline section {key} changed")
    digest = hashlib.sha256(baseline_text.encode()).hexdigest()
    if digest != record.get("baseline_sha256") or len(baseline_text.encode()) != record.get("baseline_bytes"):
        fail("inventory baseline bytes differ from migration_record.baseline_sha256 (baseline must stay immutable)")
    if record.get("independent_semantic_review") != "pending":
        fail("independent_semantic_review must stay pending until an independent reviewer passes it")
    return baseline, record


_blob_cache: dict[str, list[str] | None] = {}


def baseline_lines(inv: dict, bundle_path: str):
    if bundle_path in _blob_cache:
        return _blob_cache[bundle_path]
    blob = next((f["blob"] for f in inv["files"] if f["path"] == bundle_path), None)
    lines = None
    if blob:
        try:
            out = subprocess.run(["git", "cat-file", "blob", blob], cwd=ROOT, capture_output=True,
                                 text=True, check=True).stdout
            lines = out.split("\n")
        except (OSError, subprocess.CalledProcessError):
            lines = None
    _blob_cache[bundle_path] = lines
    return lines


def expected_nuance(inv, policy, bundle, record):
    subs = record["layout"]["source_nuance_substitutions"]
    refmap = record["layout"]["reference_map"]
    out = []
    for src in policy["sources"]:
        if src["bundle"] not in ("both", bundle):
            continue
        path = src["path"]
        if "{,-copilot}" in path:
            path = path.replace("{,-copilot}", SUFFIX[bundle])
        elif src["bundle"] == "both" and path.startswith("agents/") and bundle == "copilot" \
                and not path.endswith("-copilot.md"):
            path = path[:-3] + "-copilot.md"
        if "doc-format-templates" in path:
            continue
        lines = baseline_lines(inv, BUNDLE_PREFIX[bundle] + path)
        if lines is None:
            return None
        start, _, end = str(src["lines"]).partition("-")
        text = "\n".join(lines[int(start) - 1:int(end or start)])
        for sub in subs:
            if sub["replacement"] == "REFMAP":
                text = re.sub(sub["pattern"], lambda m: "`%s`" % refmap[m.group(1) + ".md"], text)
            else:
                text = re.sub(sub["pattern"], sub["replacement"], text)
        out.append({"path": path, "lines": str(src["lines"]), "text": text + "\n"})
    return out


# --------------------------------------------------------------------------- content audit
def audit_bundle(bundle: str, inv: dict, record: dict, counts: dict) -> dict:
    root = BUNDLES[bundle]
    policies = {p["id"]: p for p in inv["policies"]}
    decisions = record["conflict_decisions"]
    pch_affects = {}
    for pc in inv["planned_changes"]:
        for target in pc.get("affects", []):
            pch_affects.setdefault(target, set()).add(pc["id"])
    try:
        manifest = load_file(root / "policies/manifest.yaml")
    except ValueError as exc:
        fail(f"{bundle}: {exc}")
        return {}
    if manifest.get("bundle") != bundle:
        fail(f"{bundle}: manifest bundle mismatch")
    listed = set(manifest["files"]) | {"policies/manifest.yaml"}
    on_disk = {str(p.relative_to(root)) for p in (root / "policies").rglob("*.yaml")}
    on_disk |= {str(p.relative_to(root)) for p in (root / "skills").glob("*/references/workflow.yaml")}
    if listed != on_disk:
        fail(f"{bundle}: manifest files {sorted(listed ^ on_disk)} differ from YAML on disk")
    docs = {}
    for rel in sorted(on_disk):
        try:
            data = load_file(root / rel)
        except ValueError as exc:
            fail(f"{bundle}/{rel}: {exc}")
            continue
        docs[rel] = data
        if data.get("bundle") != bundle or data.get("schema_version") != "1.0":
            fail(f"{bundle}/{rel}: header bundle/schema_version invalid")
    actual_index = {}
    for rel, data in docs.items():
        for pid in (data.get("policies") or {}):
            if pid in actual_index:
                fail(f"{bundle}: policy {pid} defined twice")
            actual_index[pid] = rel
        declared = manifest["files"].get(rel, {}).get("policies", []) if rel != "policies/manifest.yaml" else []
        if rel != "policies/manifest.yaml" and list((data.get("policies") or {})) != declared:
            fail(f"{bundle}/{rel}: manifest files[].policies differs from file content")
    if manifest.get("policy_index") != actual_index:
        fail(f"{bundle}: manifest policy_index does not match file contents")

    fm_record = record["final_mapping"]
    rule_amends = record["rule_amendments"]
    added = record["added_rules"]
    migrated_rules = 0
    nuance_checked = nuance_unavailable = 0
    for pid, base in policies.items():
        fmap = fm_record.get(pid)
        if fmap is None:
            fail(f"migration_record.final_mapping missing {pid}")
            continue
        entry = fmap["bundles"][bundle]
        pol_am = fmap.get("policy_amendment")
        changed = set(pol_am["changed"]) if pol_am else set()
        if pid not in actual_index:
            if entry["status"] != "not-applicable":
                fail(f"{bundle}: policy {pid} missing (mapping says {entry['status']})")
            if bundle in base["scope"]["platforms"] and "scope.platforms" not in changed:
                fail(f"{bundle}: in-scope policy {pid} missing")
            if pid not in manifest.get("not_applicable", {}):
                fail(f"{bundle}: absent policy {pid} not declared not_applicable")
            continue
        rel = actual_index[pid]
        if entry.get("file") != rel:
            fail(f"{bundle}: mapping file for {pid} is {entry.get('file')} but policy lives in {rel}")
        rec = docs[rel]["policies"][pid]
        extra = set(rec) - POLICY_KEYS
        if extra:
            fail(f"{bundle}:{pid}: unexpected policy keys {sorted(extra)}")
        for key in ("title", "kind", "exceptions"):
            if rec.get(key) != base[key]:
                fail(f"{bundle}:{pid}: {key} differs from baseline")
        scope = copy.deepcopy(rec.get("scope"))
        base_scope = copy.deepcopy(base["scope"])
        for ch in changed:
            if ch.startswith("scope."):
                scope.pop(ch[6:], None)
                base_scope.pop(ch[6:], None)
        if scope != base_scope:
            fail(f"{bundle}:{pid}: scope differs from baseline (undeclared)")
        if bundle not in rec["scope"]["platforms"]:
            fail(f"{bundle}:{pid}: present in bundle outside its scope.platforms")
        if "defaults" not in changed and rec.get("defaults") != project_value(base["defaults"], bundle):
            fail(f"{bundle}:{pid}: defaults differ from baseline")
        if "platform_binding" not in changed:
            want = project_value(base["platform_variants"], bundle) if base.get("platform_variants") else None
            if rec.get("platform_binding") != want:
                fail(f"{bundle}:{pid}: platform_binding differs from baseline platform_variants")
        if pol_am:
            if rec.get("amendment") != {"by": pol_am["by"], "reason": pol_am["reason"], "changed": pol_am["changed"]}:
                fail(f"{bundle}:{pid}: policy amendment block does not match migration_record")
        elif "amendment" in rec:
            fail(f"{bundle}:{pid}: undeclared policy amendment")
        want_res = {k: v["decision"] for k, v in decisions.items() if pid in v["applied_to"]}
        if (rec.get("resolutions") or {}) != want_res:
            fail(f"{bundle}:{pid}: resolutions differ from migration_record conflict decisions")
        want_pc = sorted(pch_affects.get(pid, ()))
        if sorted(rec.get("planned_changes") or {}) != want_pc:
            fail(f"{bundle}:{pid}: planned_changes keys differ from inventory affects")
        want_rp = [(r["path"], r["content"]) for r in fmap.get("retained_prose", [])]
        got_rp = [(r["path"].replace("-copilot.md", ".md"), r["content"]) for r in rec.get("retained_prose", [])]
        if want_rp != got_rp or any(not nonempty(r.get("reason")) for r in rec.get("retained_prose", [])):
            fail(f"{bundle}:{pid}: retained_prose differs from migration_record")
        nuance = expected_nuance(inv, base, bundle, record)
        if nuance is None:
            nuance_unavailable += 1
        else:
            nuance_checked += 1
            if (rec.get("source_nuance") or []) != nuance:
                fail(f"{bundle}:{pid}: source_nuance differs from baseline excerpt + declared substitutions")

        # rules
        rules = rec.get("rules") or {}
        expected = {}
        for rule in base["rules"]:
            proj = project_rule(rule, bundle)
            if proj is None:
                continue
            am = rule_amends.get(rule["id"])
            if am:
                for k in am["removed_fields"]:
                    proj.pop(k, None)
                proj.update(copy.deepcopy(am["set"]))
                proj["amendment"] = {"by": am["by"], "reason": am["reason"]}
            expected[rule["id"]] = proj
        for rid, info in added.items():
            if info["policy"] == pid:
                expected[rid] = None
        if set(rules) != set(expected):
            fail(f"{bundle}:{pid}: rule IDs differ: missing {sorted(set(expected) - set(rules))}, "
                 f"extra {sorted(set(rules) - set(expected))}")
        for rid, got in rules.items():
            if rid not in expected:
                continue
            if not isinstance(got, dict):
                fail(f"{bundle}:{rid}: rule is not a mapping")
                continue
            content = {k: v for k, v in got.items() if k not in NON_CONTENT}
            if not any(nonempty(v) for v in content.values()):
                fail(f"{bundle}:{rid}: empty rule content")
            for key, val in (got.get("resolution") or {}).items():
                if key in decisions:
                    if pid not in decisions[key]["applied_to"]:
                        fail(f"{bundle}:{rid}: resolution {key} not applied to {pid} in migration_record")
                elif key not in record["planned_change_decisions"]:
                    fail(f"{bundle}:{rid}: unknown resolution key {key}")
                if not nonempty(val):
                    fail(f"{bundle}:{rid}: empty resolution {key}")
            if expected[rid] is None:
                if got.get("added_by") != added[rid]["by"]:
                    fail(f"{bundle}:{rid}: added_by does not match migration_record")
            else:
                cmp = {k: v for k, v in got.items() if k not in ("resolution", "frontmatter_exact")}
                if cmp != expected[rid]:
                    fail(f"{bundle}:{rid}: rule content differs from baseline projection/declared amendment")
        migrated_rules += len(rules)
        if entry.get("rules") != len(rules) or entry.get("status") not in ("migrated", "migrated-with-retained-prose"):
            fail(f"{bundle}:{pid}: final_mapping status/rule count stale")
        counts.setdefault("rule_ids", set()).update(rules)
    stale = set(actual_index) - set(policies)
    if stale:
        fail(f"{bundle}: stale policy declarations {sorted(stale)}")
    counts[bundle] = {"policies": len(actual_index), "rules": migrated_rules,
                      "nuance_checked": nuance_checked, "nuance_unavailable": nuance_unavailable}
    return {"manifest": manifest, "docs": docs, "index": actual_index}


def audit_load_sets(bundle: str, state: dict, inv: dict) -> None:
    root = BUNDLES[bundle]
    manifest, docs, index = state["manifest"], state["docs"], state["index"]
    sets = manifest["load_sets"]
    bindings = manifest["actor_bindings"]
    unbound = manifest.get("unbound_actors", {})
    for name, ls in sets.items():
        for rel in ls["files"]:
            if not (root / rel).is_file():
                fail(f"{bundle}: load set {name} names missing file {rel}")
    for actor, targets in bindings.items():
        for t in targets:
            if t not in sets:
                fail(f"{bundle}: actor {actor} bound to unknown load set {t}")
    for pid, rel in index.items():
        for actor in docs[rel]["policies"][pid]["scope"]["actors"]:
            if actor in unbound:
                if not nonempty(unbound[actor]):
                    fail(f"{bundle}: unbound actor {actor} lacks a reason")
                continue
            if actor not in bindings:
                fail(f"{bundle}: actor {actor!r} of {pid} has no load-set binding")
                continue
            for t in bindings[actor]:
                if t in sets and rel not in sets[t]["files"]:
                    fail(f"{bundle}: load set {t} (actor {actor}) lacks {rel} needed by {pid}")
    need = {"host.models": ["policies/models.yaml", "policies/commands.yaml"],
            "host.update": ["policies/update.yaml", "policies/install.yaml"],
            # CTX-RES-001 builds $RESOURCE_RESEARCH_CONTEXT from TSP-* by meaning (no literal ID), so it is pinned here.
            "host.launch": ["policies/models.yaml", "policies/bootstrap.yaml", "policies/trusted-sources.yaml"],
            "controller": [f"skills/{s}/references/workflow.yaml" for s in SKILLS]
            + ["policies/agents/dev-dude-orchestrator.yaml", "policies/handoff.yaml", "policies/models.yaml"]}
    for s in SKILLS:
        need[f"stage.{s}"] = [f"skills/{s}/references/workflow.yaml", "policies/handoff.yaml", "policies/models.yaml"]
    for r in ROLE_CODES.values():
        if r != "dev-dude-orchestrator":
            need[f"specialist.{r}"] = [f"policies/agents/{r}.yaml", "policies/handoff.yaml", "policies/platform.yaml",
                                       "policies/state.yaml"]
    need["stage.dev-dude-architecture"].append("policies/runtime-context.yaml")
    need["stage.dev-dude-feature-design"].append("skills/dev-dude-architecture/references/workflow.yaml")
    for name, files in need.items():
        if name not in sets:
            fail(f"{bundle}: load set {name} missing")
            continue
        for rel in files:
            if rel not in sets[name]["files"]:
                fail(f"{bundle}: load set {name} lacks {rel}")
    # consumer stubs
    platform = docs["policies/platform.yaml"]
    locs = platform["root_locations"]
    candidates = [locs[k] + "/policies/manifest.yaml" for k in ("project", "user") if k in locs]
    for role in ROLE_CODES.values():
        path = root / "agents" / f"{role}{SUFFIX[bundle]}.md"
        _, body = frontmatter(path)
        lset = "controller" if role == "dev-dude-orchestrator" else f"specialist.{role}"
        if f"manifest load set `{lset}`" not in body or f"policies/agents/{role}.yaml" not in body:
            fail(f"{bundle}: {path.name} loader does not reference load set {lset} and its role file")
        found = re.findall(r"^\s+- `([^`]+/policies/manifest\.yaml)`", body, flags=re.M)
        if found != candidates:
            fail(f"{bundle}: {path.name} root candidates {found} != platform root_locations {candidates}")
        heads = re.findall(r"^## (.+)$", strip_fences(body), flags=re.M)
        if [h for h in heads if h not in ("Policy Loading (required before any work)", "Examples (nonnormative)")]:
            fail(f"{bundle}: {path.name} still has normative sections {heads}")
        if "POLICY ROOT GATE" not in body:
            fail(f"{bundle}: {path.name} lacks POLICY ROOT GATE")
    for s in SKILLS:
        _, body = frontmatter(root / "skills" / s / "SKILL.md")
        for needle in (f"stage.{s}", "policy_context", "POLICY ROOT GATE", "STAGE VERSION GATE"):
            if needle not in body:
                fail(f"{bundle}: skills/{s}/SKILL.md lacks {needle}")
        md = root / "skills" / s / "references/workflow.md"
        if md.exists():
            text = md.read_text(encoding="utf-8")
            if "Nonnormative examples only" not in text or \
                    any(not h.startswith("Example: ") for h in re.findall(r"^## (.+)$", strip_fences(text), flags=re.M)):
                fail(f"{bundle}: {md.relative_to(ROOT)} contains non-example sections")
    _, body = frontmatter(root / "SKILL.md")
    for pid in set(re.findall(r"\b[A-Z]{2,5}(?:-[A-Z0-9]+)*-\d{3}\b", body)):
        if pid not in index:
            fail(f"{bundle}: root SKILL.md cites unknown policy {pid}")
    for name in ("host.models", "host.update", "host.launch", "controller"):
        if f"`{name}`" not in body:
            fail(f"{bundle}: root SKILL.md does not name load set {name}")
    for needle in ("root_discovery", "POLICY ROOT GATE", "POLICY LOAD GATE", "launch_validation"):
        if needle not in body:
            fail(f"{bundle}: root SKILL.md lacks {needle}")


def audit_frontmatter(bundle: str, state: dict) -> None:
    root = BUNDLES[bundle]
    md = state["docs"]["policies/metadata.yaml"]
    models = state["docs"]["policies/models.yaml"]
    pol = md["policies"]

    def resolve(rule):
        if "value_ref" in rule:
            return get_path(md, rule["value_ref"])
        if "version_ref" in rule:
            return get_path(md, rule["version_ref"])
        return rule.get("value")

    names = []
    for code, role in ROLE_CODES.items():
        path = root / "agents" / f"{role}{SUFFIX[bundle]}.md"
        names.append(path.stem)
        fm, body = frontmatter(path)
        text = path.read_text(encoding="utf-8")
        if len(re.findall(r"^version:\s*(.+)$", text, flags=re.M)) != 1:
            fail(f"{bundle}: {path.name} must have exactly one '^version:' line (bump workflow regex)")
        for rid, rule in pol[f"AGT-{code}-META-001"]["rules"].items():
            key = rule.get("key")
            if key == "description":
                if rule.get("frontmatter_exact") != fm.get("description"):
                    fail(f"{bundle}: {rid} frontmatter_exact != {path.name} description")
                continue
            if key not in ("name", "model", "version", "color", "tools"):
                continue
            want, got = resolve(rule), fm.get(key)
            if key == "tools" and isinstance(want, str) and want.startswith("unrestricted"):
                want = None  # baseline records "no tools key" as unrestricted
            if key == "tools" and isinstance(got, str):
                got = [t.strip() for t in got.split(",")]
            if want != got:
                fail(f"{bundle}: {rid} {key}={want!r} but {path.name} has {got!r}")
        if models["bundled_default"]["models"].get(role) != fm.get("model"):
            fail(f"{bundle}: models.yaml bundled_default {role} != {path.name} model")
    if sorted(md["crews"]["agents"]["names"]) != sorted(names):
        fail(f"{bundle}: crews.agents.names differ from agent files")
    if list(models["bundled_default"]["models"]) != models["roles"]["dispatch"]:
        fail(f"{bundle}: bundled_default roles differ from roles.dispatch")
    if models["bundled_default"]["critique"] is not None:
        fail(f"{bundle}: bundled_default critique must stay null (legacy stronger-model rule)")
    fm, body = frontmatter(root / "SKILL.md")
    for rule in pol["META-ROOT-001"]["rules"].values():
        if rule["key"] == "description":
            if rule.get("frontmatter_exact") != fm.get("description"):
                fail(f"{bundle}: META-ROOT-001 description != root frontmatter")
        elif resolve(rule) != fm.get(rule["key"]):
            fail(f"{bundle}: META-ROOT-001 {rule['key']} != root frontmatter")
    hints = re.findall(r"^  - (.+)$", body.split("\n# ")[0], flags=re.M)
    if hints != md["root"]["argument_hint_display"]:
        fail(f"{bundle}: root argument-hint lines differ from metadata root.argument_hint_display")
    for label, ref in (("agent", "crews.agents.version"), ("skill", "crews.skills.version")):
        found = re.findall(rf"Bundled {label} crew version: `([^`]+)`", body)
        if found != [get_path(md, ref)]:
            fail(f"{bundle}: root SKILL.md {label} crew sentence {found} != {ref}")
    for pid in ("META-SKL-001", "FSK-META-001"):
        for rid, rule in pol[pid]["rules"].items():
            if "skill" not in rule:
                continue
            sfm, _ = frontmatter(root / "skills" / rule["skill"] / "SKILL.md")
            if sfm.get("name") != rule["skill"] or str(sfm.get("version")) != resolve(rule):
                fail(f"{bundle}: {rid} name/version != skill frontmatter")
            if rule.get("frontmatter_exact") != sfm.get("description") or \
                    " ".join(str(rule.get("description")).split()) != " ".join(str(sfm.get("description")).split()):
                fail(f"{bundle}: {rid} description != skill frontmatter")


CREW_GLOBS = ("agents/*.md", "policies/agents/*.yaml", "policies/models.yaml")


def _glob_re(glob: str):
    # GitHub Actions paths filter: `*` matches any character except `/`.
    return re.compile("^" + "".join("[^/]*" if ch == "*" else re.escape(ch) for ch in glob) + "$")


def load_bump_script(text: str):
    """Exec the workflow's embedded Python with a non-main __name__ so main() does not run."""
    m = re.search(r"python <<'PY'\n(.*?)\n\s*PY\n", text, flags=re.S)
    if not m:
        fail("bump workflow embedded Python (python <<'PY' ... PY) not found")
        return None
    lines = m.group(1).split("\n")
    indent = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
    src = "\n".join(l[indent:] for l in lines)
    try:
        code = compile(src, "bump-agent-versions.yml:embedded", "exec")
    except SyntaxError as exc:
        fail(f"bump workflow embedded Python does not compile: {exc}")
        return None
    ns = {"__name__": "policy_audit_bump_workflow"}
    exec(code, ns)
    for name in ("is_crew_change", "bump_agent_text", "bump_skill_text", "bump_metadata_text", "main"):
        if not callable(ns.get(name)):
            fail(f"bump workflow embedded Python lacks function {name}")
            return None
    if "if __name__ == '__main__':" not in src:
        fail("bump workflow embedded Python must guard main() with __name__")
    return ns


def audit_bump_workflow() -> int:
    """Checks trigger paths, changed-file filter, bump functions and loop guard; returns checks run."""
    checks = 0
    text = WORKFLOW.read_text(encoding="utf-8")
    try:
        wf = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        fail(f"bump workflow YAML invalid: {exc}")
        return checks
    on = wf.get("on", wf.get(True)) or {}
    trigger = list((on.get("push") or {}).get("paths") or [])
    expected = [BUNDLE_PREFIX[b] + g for g in CREW_GLOBS for b in ("copilot", "claude")]
    checks += 1
    if sorted(trigger) != sorted(expected):
        fail(f"bump workflow on.push.paths {trigger} != agent-crew globs {expected}")
    for bundle, root in BUNDLES.items():
        vb = load_file(root / "policies/metadata.yaml").get("version_bump") or {}
        checks += 1
        if sorted(vb.get("trigger_paths") or []) != sorted(trigger):
            fail(f"{bundle}: metadata.yaml version_bump.trigger_paths differ from workflow on.push.paths")
        for key in ("filter", "writes", "never_writes", "manual", "loop_guard"):
            if not vb.get(key):
                fail(f"{bundle}: metadata.yaml version_bump.{key} missing")
    job = next(iter((wf.get("jobs") or {}).values()), {})
    cond = str(job.get("if", ""))
    checks += 1
    if "github.actor != 'github-actions[bot]'" not in cond or "[skip agent-version-bump]" not in cond:
        fail("bump workflow job lacks the bot-actor / skip-tag loop guard")
    ns = load_bump_script(text)
    if ns is None:
        return checks
    if "[skip agent-version-bump]" not in text.split("message = ", 1)[-1].split("\n", 1)[0]:
        fail("bump workflow commit message lacks [skip agent-version-bump]")
    globs = [_glob_re(g) for g in trigger]
    candidates = set()
    for bundle, root in BUNDLES.items():
        for f in root.rglob("*"):
            if f.is_file():
                candidates.add(str(f.relative_to(ROOT)))
        for extra in ("agents/sub/x.md", "policies/agents/sub/x.yaml", "policies/metadata.yaml", "policies/models.yml",
                      "agents/x.yaml", "skills/dev-dude-validation/SKILL.md", "SKILL.md", "policies/agents.yaml"):
            candidates.add(BUNDLE_PREFIX[bundle] + extra)
    candidates |= {"README.md", "policy-migration-inventory.yaml", "Other/dev-dude/agents/x.md",
                   "x/Copilot/dev-dude/agents/x.md"}
    hits = 0
    for path in sorted(candidates):
        want = any(g.match(path) for g in globs)
        hits += want
        checks += 1
        if bool(ns["is_crew_change"](path)) != want:
            fail(f"bump workflow filter disagrees with trigger paths for {path!r} (trigger={want})")
    if hits < 2 * (9 + 9 + 1):
        fail(f"bump workflow trigger covers only {hits} bundle files (expected agents, role policies, models.yaml)")
    for bundle, root in BUNDLES.items():
        written = [root / "policies/metadata.yaml", root / "SKILL.md"] + sorted((root / "agents").glob("*.md"))
        for w in written:
            checks += 1
            if not ns["is_crew_change"](str(w.relative_to(ROOT))) and w.parent.name == "agents":
                fail(f"{w}: agent file not a crew change")
        for w in (root / "policies/metadata.yaml", root / "SKILL.md"):
            if ns["is_crew_change"](str(w.relative_to(ROOT))):
                fail(f"{w}: bump output is itself a trigger path (loop)")
        mtext = (root / "policies/metadata.yaml").read_text(encoding="utf-8")
        before = strict_load(mtext)
        after = strict_load(ns["bump_metadata_text"](mtext, "9.9.9", "metadata"))
        checks += 1
        if after["crews"]["agents"]["version"] != "9.9.9":
            fail(f"{bundle}: workflow bump_metadata_text does not set crews.agents.version")
        after["crews"]["agents"]["version"] = before["crews"]["agents"]["version"]
        if after != before:
            fail(f"{bundle}: workflow bump_metadata_text changes more than crews.agents.version")
        stext = (root / "SKILL.md").read_text(encoding="utf-8")
        snew = ns["bump_skill_text"](stext, "9.9.9")
        checks += 1
        if len(re.findall(r"Bundled agent crew version:\s*`[^`]+`", stext)) != 1:
            fail(f"{bundle}: root SKILL.md agent crew sentence must appear once")
        if snew == stext or snew.replace("Bundled agent crew version: `9.9.9`", "") != re.sub(
                r"Bundled agent crew version:\s*`[^`]+`", "", stext):
            fail(f"{bundle}: workflow bump_skill_text must change only the agent crew sentence")
        if fm_of(snew) != fm_of(stext):
            fail(f"{bundle}: workflow bump_skill_text changed root frontmatter (root version is manual)")
        for agent in sorted((root / "agents").glob("*.md")):
            atext = agent.read_text(encoding="utf-8")
            anew = ns["bump_agent_text"](atext, "9.9.9", agent)
            checks += 1
            diff = [(a, b) for a, b in zip(atext.split("\n"), anew.split("\n")) if a != b]
            if len(atext.split("\n")) != len(anew.split("\n")) or len(diff) != 1 \
                    or diff[0][1] != "version: 9.9.9":
                fail(f"{agent.relative_to(ROOT)}: workflow bump_agent_text must change only the version line")
    return checks


def fm_of(text: str) -> str:
    m = re.match(r"---\n(.*?)\n---\n", text, flags=re.S)
    return m.group(1) if m else ""


def audit_workflow_and_links(states: dict) -> None:
    pattern = re.compile(r"\b(" + "|".join(re.escape(d) for d in DELETED) + r")\b")
    link = re.compile(r"(?:\]\(|references/)[^)\s`'\"]*?(" + "|".join(re.escape(d) for d in DELETED) + r")")
    scan = [README] + [p for b in BUNDLES.values() for p in b.rglob("*.md")]
    for p in scan:
        for m in pattern.finditer(p.read_text(encoding="utf-8")):
            fail(f"{p.relative_to(ROOT)} still references deleted {m.group(1)}")
    for bundle, state in states.items():
        for rel, data in state["docs"].items():
            for pid, rec in (data.get("policies") or {}).items():
                blob = json.dumps({k: v for k, v in rec.items() if k != "source_nuance"})
                for m in link.finditer(blob):
                    fail(f"{bundle}/{rel}:{pid} rule content references deleted {m.group(1)}")
    for b in BUNDLES.values():
        for d in DELETED[:-1]:
            if (b / "references" / d).exists():
                fail(f"{b.relative_to(ROOT)}/references/{d} should be deleted")
    readme = README.read_text(encoding="utf-8")
    for needle, why in (("except `update`", "PCH-UPD-001 update-check exception"),
                        ("offline `models` commands", "PCH-UPD-001 models exception"),
                        (".docx", "CNF-DRIFT-002"), ("optional on GitHub Copilot", "CNF-IDX-001"),
                        ("/dev-dude models validate", "models validate documented")):
        if needle not in readme:
            fail(f"README lacks {needle!r} ({why})")


def audit_record(inv, record, counts) -> None:
    if set(record["conflict_decisions"]) != {c["id"] for c in inv["conflicts"]}:
        fail("conflict_decisions do not cover exactly the 25 inventory conflicts")
    pids = {p["id"] for p in inv["policies"]}
    for cid, d in record["conflict_decisions"].items():
        if d["status"] not in ("resolved", "preserved") or not nonempty(d["decision"]) or not nonempty(d["evidence"]):
            fail(f"{cid}: incomplete decision")
        for pid in d["applied_to"]:
            if pid not in pids:
                fail(f"{cid}: applied_to unknown policy {pid}")
    if set(record["planned_change_decisions"]) != {p["id"] for p in inv["planned_changes"]}:
        fail("planned_change_decisions do not cover the inventory planned changes")
    for pc, d in record["planned_change_decisions"].items():
        for part in re.split(r"[;,]\s*", d["destination"]):
            if not part.startswith("policies/"):
                continue
            rel, _, key = part.partition("#")
            for bundle, root in BUNDLES.items():
                try:
                    get_path(load_file(root / rel), key)
                except (KeyError, ValueError):
                    fail(f"{pc}: destination {part} missing in {bundle}")
    base_ids = {r["id"] for p in inv["policies"] for r in p["rules"]}
    if base_ids - counts["rule_ids"]:
        fail(f"baseline rules not migrated: {sorted(base_ids - counts['rule_ids'])}")
    c = record["counts"]
    if c["baseline_rules_migrated"] != len(base_ids & counts["rule_ids"]) or c["baseline_rules_not_migrated"]:
        fail("migration_record.counts stale")
    for bundle in BUNDLES:
        if c[bundle] != {"policies": counts[bundle]["policies"], "rules": counts[bundle]["rules"]}:
            fail(f"migration_record.counts.{bundle} stale")
    if sorted(counts["rule_ids"] - base_ids) != sorted(record["added_rules"]):
        fail("added rules differ from migration_record.added_rules")


def audit_reconciliation(record, states) -> dict:
    """Counts and record copies must agree with the YAML actually on disk."""
    amended_yaml, added_yaml = set(), set()
    for state in states.values():
        for data in state["docs"].values():
            for rec in (data.get("policies") or {}).values():
                for rid, rule in (rec.get("rules") or {}).items():
                    if "amendment" in rule:
                        amended_yaml.add(rid)
                    if "added_by" in rule:
                        added_yaml.add(rid)
    c = record["counts"]
    fmap_amended = {r for v in record["final_mapping"].values() for r in v.get("amended_rules", [])}
    sources = {"counts.amended_rules": set(c["amended_rules"]), "rule_amendments": set(record["rule_amendments"]),
               "final_mapping amended_rules": fmap_amended, "YAML amendment blocks": amended_yaml}
    if len({frozenset(v) for v in sources.values()}) != 1 or len(c["amended_rules"]) != len(set(c["amended_rules"])):
        fail("amended-rule counts disagree: " + ", ".join(f"{k}={len(v)}" for k, v in sources.items()))
    if not (set(c["added_rules"]) == set(record["added_rules"]) == added_yaml):
        fail(f"added-rule counts disagree: counts={len(c['added_rules'])} record={len(record['added_rules'])} "
             f"YAML={len(added_yaml)}")
    for bundle, state in states.items():
        m = state["manifest"]
        if m.get("source_nuance_substitutions") != record["layout"]["source_nuance_substitutions"] or \
                m.get("reference_map") != record["layout"]["reference_map"]:
            fail(f"{bundle}: manifest source_nuance_substitutions/reference_map differ from migration_record.layout")
    stale = re.compile(r"(?m)^version: \d+\.\d+\.\d+$|crew version: `\d|\]\(references/workflow\.md\)|"
                       r"shared-policy paths under this root's `references/`|this skill and its references supply")
    for bundle, state in states.items():
        for rel, data in state["docs"].items():
            for pid, rec in (data.get("policies") or {}).items():
                for n in rec.get("source_nuance") or []:
                    if stale.search(n["text"]):
                        fail(f"{bundle}/{rel}:{pid} source_nuance keeps stale wording {stale.search(n['text']).group(0)!r}")
    abs_ = (record.get("architecture_decisions") or {}).get("agent_body_strategy") or {}
    if abs_.get("selected") != "ABS-B" or "ABS-A" not in str(abs_.get("baseline_recommendation")) or \
            len(abs_.get("rationale") or []) < 3 or not nonempty(abs_.get("behavior_change")) or not nonempty(abs_.get("approval")):
        fail("migration_record.architecture_decisions.agent_body_strategy must record ABS-B, rationale and behavior change")
    review = (record.get("review_amendments") or {}).get("items") or {}
    if len(review) != 9 or not all(nonempty(v) for v in review.values()):
        fail("migration_record.review_amendments must record all nine review items")
    if "pending" not in str((record.get("review_amendments") or {}).get("status")):
        fail("review_amendments must stay pending independent review")
    return {"amended": len(amended_yaml), "added": len(added_yaml)}


# --------------------------------------------------------------------------- model helpers
PID_RE = re.compile(r"\b([A-Z]{2,5}(?:-[A-Z0-9]+)*-\d{3})(?:\.R\d+[a-z]?)?\b")
PATH_RE = re.compile(r"\b(policies/[a-z0-9/-]+\.yaml|skills/dev-dude-[a-z-]+/references/workflow\.yaml)\b")


def audit_load_set_closure(bundle: str, state: dict) -> int:
    """Every policy or YAML file named by a policy an actor applies must be in that actor's load set,
    unless manifest informative_references declares the reference non-operative."""
    manifest, docs, index = state["manifest"], state["docs"], state["index"]
    sets, bindings = manifest["load_sets"], manifest["actor_bindings"]
    informative = manifest.get("informative_references") or {}
    for key, why in informative.items():
        src, _, dst = key.partition("->")
        if src not in index and src not in state.get("conflict_ids", ()) or dst not in index or not nonempty(why):
            fail(f"{bundle}: informative_references {key} is not SRC->policy with a reason")
    checked = 0
    for name, ls in sets.items():
        files = set(ls["files"]) | {"policies/manifest.yaml"}
        actors = {a for a, ts in bindings.items() if name in ts}
        for rel in ls["files"]:
            for pid, rec in (docs.get(rel, {}).get("policies") or {}).items():
                if not actors & set(rec["scope"]["actors"]):
                    continue
                blob = json.dumps({k: v for k, v in rec.items() if k != "source_nuance"})
                srcs = {pid} | set((rec.get("resolutions") or {}))
                for m in PID_RE.finditer(blob):
                    target = m.group(1)
                    checked += 1
                    if target not in index or index[target] in files:
                        continue
                    if any(f"{s}->{target}" in informative for s in srcs):
                        continue
                    fail(f"{bundle}: load set {name}: {pid} names {m.group(0)} in {index[target]}, not in the load set")
                for m in PATH_RE.finditer(blob):
                    checked += 1
                    if m.group(1) not in files and m.group(1) in docs:
                        fail(f"{bundle}: load set {name}: {pid} names {m.group(1)}, not in the load set")
    return checked


INTEGRITY_KEYS = ["purpose", "hashing", "policy_snapshot", "verification", "migration", "standalone", "limits"]
ENV_POLICY_FIELDS = ["Policy manifest", "Policy manifest digest", "Policy snapshot", "Policy snapshot digest",
                     "Model profile snapshot", "Model profile digest"]
HOC_POLICY_FIELDS = ["policy_root", "policy_manifest", "manifest_digest", "policy_snapshot", "policy_snapshot_digest",
                     "model_profile_snapshot", "model_profile_digest"]


def audit_integrity(bundle: str, state: dict) -> None:
    root, docs, manifest = BUNDLES[bundle], state["docs"], state["manifest"]
    integ = manifest.get("integrity") or {}
    if list(integ) != INTEGRITY_KEYS:
        fail(f"{bundle}: manifest integrity keys {list(integ)} != {INTEGRITY_KEYS}")
        return
    ps = integ["policy_snapshot"]
    contents = " ".join(ps.get("contents", []))
    for needle in ("bundle_revision", "sha256", "policies/manifest.yaml", "hashing command"):
        if needle not in contents:
            fail(f"{bundle}: integrity.policy_snapshot.contents lacks {needle}")
    if ps.get("file") != "<run-output>/.dev-dude-policy-snapshot.yaml" or "host" not in ps.get("computed_by", "") \
            or "controller" not in ps.get("written_by", ""):
        fail(f"{bundle}: integrity.policy_snapshot file/computed_by/written_by drifted")
    if "never estimates" not in integ["hashing"].get("honesty", "") or "POLICY INTEGRITY GATE" not in integ["hashing"]["honesty"]:
        fail(f"{bundle}: integrity.hashing.honesty must forbid model-invented hashes and stop at POLICY INTEGRITY GATE")
    ver = " ".join(integ["verification"])
    for needle in ("every resume", "POLICY INTEGRITY GATE", "VAL-PASS-001.R06", "MODEL PIN GATE", "No dispatch"):
        if needle not in ver:
            fail(f"{bundle}: integrity.verification lacks {needle!r}")
    if not any("POLICY INTEGRITY GATE" in r for r in manifest["loading"]["rules"]):
        fail(f"{bundle}: manifest loading.rules lack the integrity check")
    pol = lambda rel, pid, rid: docs[rel]["policies"][pid]["rules"][rid]  # noqa: E731
    env = pol("policies/handoff.yaml", "ENV-001", "ENV-001.R07")["fields"]
    if env != ENV_POLICY_FIELDS + ["Invocation mode"]:
        fail(f"{bundle}: ENV-001.R07 fields {env} != policy/model snapshot fields")
    hoc = pol("policies/handoff.yaml", "HOC-SCHEMA-001", "HOC-SCHEMA-001.R16")["fields"]
    if hoc != HOC_POLICY_FIELDS:
        fail(f"{bundle}: HOC-SCHEMA-001.R16 fields {hoc} != {HOC_POLICY_FIELDS}")
    st = pol("policies/state.yaml", "STATE-SCHEMA-001", "STATE-SCHEMA-001.R07")["fields"]
    if st[:-1] != ENV_POLICY_FIELDS:
        fail(f"{bundle}: STATE-SCHEMA-001.R07 fields {st} lack the policy/model snapshot fields")
    for rel, pid, rid, needle in (("policies/bootstrap.yaml", "BOOT-PKT-001", "BOOT-PKT-001.R13", "policy snapshot"),
                                  ("policies/bootstrap.yaml", "BOOT-PKT-001", "BOOT-PKT-001.R14", "policy snapshot digest"),
                                  ("policies/validation-rules.yaml", "VAL-PASS-001", "VAL-PASS-001.R06", "policy_snapshot_digest")):
        if needle not in pol(rel, pid, rid)["statement"]:
            fail(f"{bundle}: {rid} statement lacks {needle!r}")
    im = docs["policies/handoff.yaml"]["invocation_modes"]
    env_fields = pol("policies/handoff.yaml", "ENV-001", "ENV-001.R02").get("fields", [])
    labels = re.findall(r"^- ([^:]+):", im["envelope_block"], flags=re.M)
    if labels != list(env_fields) + env:
        fail(f"{bundle}: handoff envelope_block labels {labels} != ENV-001.R02 + R07 fields")
    if not any("POLICY INTEGRITY GATE" in r for r in im["orchestrated"]["rules"]):
        fail(f"{bundle}: handoff invocation_modes.orchestrated lacks the integrity re-hash")
    if not any("integrity" in r for r in docs["policies/platform.yaml"]["root_discovery"]["rules"]):
        fail(f"{bundle}: platform.yaml root_discovery does not defer to manifest integrity")
    stubs = [root / "SKILL.md"] + [root / "agents" / f"{r}{SUFFIX[bundle]}.md" for r in ROLE_CODES.values()] \
        + [root / "skills" / s / "SKILL.md" for s in SKILLS]
    for path in stubs:
        body = path.read_text(encoding="utf-8")
        if "POLICY INTEGRITY GATE" not in body or not re.search(r"[Pp]olicy[ _]snapshot", body):
            fail(f"{bundle}: {path.relative_to(root)} loader lacks the policy snapshot re-hash (POLICY INTEGRITY GATE)")
    # models.yaml: resume blocks, never revalidates; re-pin is an explicit migration
    models = docs["policies/models.yaml"]
    when = models["launch_validation"]["when"]
    if "never revalidates" not in when or "MODEL PIN GATE" not in when or "pinning.repin" not in when:
        fail(f"{bundle}: models.yaml launch_validation.when must block resume on missing/mismatched snapshot")
    for m in re.finditer(r"[^.]*\brevalidat\w*[^.]*\.", " ".join(models["pinning"]["rules"]) + " " + when):
        if not re.search(r"\bnever\b|re-pin|repin", m.group(0)):
            fail(f"{bundle}: models.yaml allows revalidation outside re-pin: {m.group(0).strip()!r}")
    pin = models["pinning"]
    if not any("policy_snapshot_digest" in c for c in pin.get("snapshot_contents", [])) or \
            not any("snapshot_version" in c for c in pin.get("snapshot_contents", [])):
        fail(f"{bundle}: models.yaml pinning.snapshot_contents lacks policy_snapshot_digest/snapshot_version")
    rp = pin.get("repin") or {}
    req = " ".join(rp.get("requires", []))
    for needle in ("quiescence", "quoted user decision", "launch_validation", "snapshot_version", "previous snapshot is kept",
                   "run-state amendment"):
        if needle not in req:
            fail(f"{bundle}: models.yaml pinning.repin.requires lacks {needle!r}")
    if "not a repair path" not in rp.get("meaning", "") or "MODEL PIN GATE" not in rp.get("otherwise", ""):
        fail(f"{bundle}: models.yaml pinning.repin must exclude tampered snapshots and block otherwise")
    # update staging validates the whole policy root
    upd = docs["policies/update.yaml"]
    r05 = upd["policies"]["UPD-CMD-001"]["rules"]["UPD-CMD-001.R05"]["statement"]
    for needle in ("policies/manifest.yaml", "every indexed file", "workflow.yaml", "escaping", "Before replacing anything"):
        if needle not in r05:
            fail(f"{bundle}: UPD-CMD-001.R05 lacks {needle!r}")


REF_SCHEMA = {"required": ["schema_version", "runtimes"], "const": "1.0", "runtimes": ["claude", "copilot"],
              "namespace": ["active_profile", "profiles"], "active_profile": "string|null"}
REF_GRAMMAR = {"models show": ("show", set()), "models profiles": ("profiles", set()), "models validate": ("validate", set()),
               "models set <role|all> <model-id> --profile <name> --scope <project|user>": ("set", {"--profile", "--scope"}),
               "models use <profile|bundled-default> --scope <project|user>": ("use", {"--scope"}),
               "models reset --scope <project|user>": ("reset", {"--scope"})}
REF_RESOLUTION = ["MODEL CONFIG GATE", "project file", "user file", "bundled-default"]
REF_GATES = {"MODEL CONFIG GATE", "MODEL CAPABILITY GATE", "MODEL PIN GATE"}
REF_PRECEDENCE = ["rule resolution entries", "rule fields", "policy resolutions", "policy defaults/exceptions",
                  "source_nuance text", "nonnormative Markdown"]


def audit_reference_parity(bundle: str, state: dict) -> int:
    """Compare the actual YAML declarations with the constants the pure reference model (ModelPolicy) assumes,
    so drift in either fails here. Consistency only; it does not prove host behaviour."""
    docs, checks = state["docs"], 0
    models, commands = docs["policies/models.yaml"], docs["policies/commands.yaml"]

    def check(ok, msg):
        nonlocal checks
        checks += 1
        if not ok:
            fail(f"{bundle}: parity: {msg}")

    sch = models["config"]["schema"]
    rts = sch["properties"]["runtimes"]
    ns = rts["values"]
    check(sch["required"] == REF_SCHEMA["required"] and sch["additional_keys"] == "reject", "schema top-level keys")
    check(sch["properties"]["schema_version"].get("const") == REF_SCHEMA["const"], "schema_version const")
    check(rts["keys"] == REF_SCHEMA["runtimes"] and rts["additional_keys"] == "reject", "runtimes namespaces")
    check(ns["required"] == REF_SCHEMA["namespace"] and ns["additional_keys"] == "reject", "namespace keys")
    check(ns["properties"]["active_profile"]["type"] == REF_SCHEMA["active_profile"], "active_profile type")
    check(ns["properties"]["profiles"]["values"]["keys"] == "roles.dispatch + critique", "profile role keys")
    check(models["roles"]["additional"] == ["critique"] and len(models["roles"]["dispatch"]) == 9, "roles")
    check(set(models["syntax"]["reserved_profile_names"]) == {"bundled-default"}, "reserved profile names")
    check({"duplicate keys", "anchors/aliases", "explicit tags", "multiple YAML documents"}
          <= set(models["config"]["limits"]["reject"]), "strict YAML rejects")
    order = models["resolution"]["order"]
    check(len(order) == len(REF_RESOLUTION) and all(n in o for n, o in zip(REF_RESOLUTION, order)),
          f"resolution order {order}")
    check(order[-1] == "bundled-default", "bundled-default is last")
    rules = " ".join(models["resolution"]["rules"])
    for needle in ("never merge", "active_profile null", "shadows lower scopes", "all nine dispatch roles and critique"):
        check(needle in rules, f"resolution rules lack {needle!r}")
    forms = [g["form"] for g in commands["models_commands"]["grammar"]]
    check(forms == list(REF_GRAMMAR), f"models grammar forms {forms}")
    mp = ModelPolicy(bundle, models, commands)
    for form, (sub, flags) in REF_GRAMMAR.items():
        toks = form.split()
        check(set(t for t in toks if t.startswith("--")) == flags, f"{form}: flags")
        concrete = [{"<role|all>": "all", "<model-id>": "vendor/m", "<name>": "team", "<project|user>": "user",
                     "<profile|bundled-default>": "bundled-default"}.get(t, t) for t in toks]
        check(mp.route(concrete) == f"models:{sub}", f"reference router rejects documented form {form}")
        if flags:
            check(mp.route(concrete[:-2]) == "models-usage", f"reference router accepts {form} without --scope")
    reset = next(g["effect"] for g in commands["models_commands"]["grammar"] if g["form"].startswith("models reset"))
    check("<file>.invalid-<N>" in reset and "first unused N" in reset, "reset quarantine naming")
    check(mp.cmd_reset("x: [", set())["renamed_to"] == "models.yaml.invalid-1", "reference quarantine name")
    usage = commands["models_commands"]["usage_text"]
    check(all(f"/dev-dude {f}" in usage for f in forms), "usage_text lists every grammar form")
    text = json.dumps(models)
    gates = set(re.findall(r"MODEL [A-Z]+ GATE", inspect.getsource(ModelPolicy)))
    check(gates == REF_GATES and all(g in text for g in gates), f"gate names {sorted(gates)}")
    meth = " ".join(models["launch_validation"]["method"])
    for needle in ("Skill tool for stages", "nested delegation for stages and feature-implementer", "write tools"):
        check(needle in meth, f"launch_validation capability {needle!r}")
    check(models["bundled_default"]["profile"] == "bundled-default" and models["bundled_default"]["critique"] is None,
          "bundled_default profile/critique")
    prec = state["manifest"]["loading"]["precedence"]
    check(len(prec) == len(REF_PRECEDENCE) and all(p.startswith(r) for p, r in zip(prec, REF_PRECEDENCE)),
          f"loading.precedence {prec}")
    md = docs["policies/metadata.yaml"]
    hints = " ; ".join(md["root"]["argument_hint_display"])
    for form in ["update"] + forms:
        head = form.split(" <")[0].split(" --")[0]
        check(head in hints, f"argument hints lack {head!r}")
    return checks


class ModelPolicy:
    """Pure reference implementation of models.yaml/commands.yaml rules for scenario checks."""

    def __init__(self, bundle: str, models: dict, commands: dict):
        self.bundle = bundle
        self.roles = list(models["roles"]["dispatch"])
        self.all_roles = self.roles + list(models["roles"]["additional"])
        syn = models["syntax"]
        self.profile_re = re.compile(syn["profile_name"])
        self.id_re = re.compile(syn["model_id"])
        self.forbidden = syn["model_id_forbidden_substrings"]
        self.aliases = set(syn["aliases_rejected_in_config"])
        self.reserved = set(syn["reserved_profile_names"])
        self.max_bytes = models["config"]["limits"]["max_bytes"]
        self.default = dict(models["bundled_default"]["models"])
        self.default_critique = models["bundled_default"]["critique"]
        self.grammar = [g["form"] for g in commands["models_commands"]["grammar"]]

    def valid_id(self, value) -> bool:
        return isinstance(value, str) and bool(self.id_re.fullmatch(value)) \
            and not any(f in value for f in self.forbidden) and value not in self.aliases

    def valid_profile_name(self, name) -> bool:
        return isinstance(name, str) and bool(self.profile_re.fullmatch(name)) and name not in self.reserved

    def parse(self, text: str):
        errs = []
        if len(text.encode()) > self.max_bytes:
            return None, ["file exceeds max_bytes"]
        try:
            data = strict_load(text)
        except ValueError as exc:
            return None, [str(exc)]
        if not isinstance(data, dict) or set(data) != {"schema_version", "runtimes"}:
            return None, ["top level must be exactly schema_version + runtimes"]
        if data["schema_version"] != "1.0":
            return None, ["unsupported schema_version"]
        rts = data["runtimes"]
        if not isinstance(rts, dict) or not set(rts) <= PLATFORMS:
            return None, ["runtimes must map claude/copilot only"]
        for rt, ns in rts.items():
            if not isinstance(ns, dict) or set(ns) != {"active_profile", "profiles"}:
                errs.append(f"{rt}: namespace keys must be active_profile + profiles")
                continue
            ap, profs = ns["active_profile"], ns["profiles"]
            if not isinstance(profs, dict):
                errs.append(f"{rt}: profiles must be a mapping")
                continue
            for name, prof in profs.items():
                if not self.valid_profile_name(name):
                    errs.append(f"{rt}: invalid profile name {name!r}")
                if not isinstance(prof, dict):
                    errs.append(f"{rt}.{name}: profile must be a mapping")
                    continue
                for role, mid in prof.items():
                    if role not in self.all_roles:
                        errs.append(f"{rt}.{name}: unknown role {role!r}")
                    elif not self.valid_id(mid):
                        errs.append(f"{rt}.{name}.{role}: invalid model id {mid!r}")
            if ap is not None and (not isinstance(ap, str) or (ap != "bundled-default" and ap not in profs)):
                errs.append(f"{rt}: active_profile must be null, bundled-default, or an existing profile")
        return (None, errs) if errs else (data, [])

    def resolve(self, project: str | None, user: str | None) -> dict:
        parsed = {}
        for scope, text in (("project", project), ("user", user)):
            if text is not None:
                data, errs = self.parse(text)
                if errs:
                    return {"status": "blocked", "gate": "MODEL CONFIG GATE", "scope": scope, "errors": errs}
                parsed[scope] = data
        for scope in ("project", "user"):
            ns = parsed.get(scope, {}).get("runtimes", {}).get(self.bundle) if scope in parsed else None
            if ns and ns["active_profile"] is not None:
                name = ns["active_profile"]
                if name == "bundled-default":
                    return self._default(scope)
                prof = ns["profiles"][name]
                if set(prof) != set(self.all_roles):
                    return {"status": "blocked", "gate": "MODEL CONFIG GATE", "scope": scope,
                            "errors": [f"profile {name} incomplete"]}
                return {"status": "ok", "profile": name, "scope": scope,
                        "models": {r: prof[r] for r in self.roles}, "critique": prof["critique"]}
        return self._default("bundled")

    def _default(self, scope):
        return {"status": "ok", "profile": "bundled-default", "scope": scope,
                "models": dict(self.default), "critique": self.default_critique}

    def route(self, tokens: list[str]) -> str:
        if tokens == ["update"]:
            return "update"
        if len(tokens) == 2 and tokens[1] == "refresh":
            return f"refresh:{tokens[0]}"
        if tokens and tokens[0] == "models":
            rest = tokens[1:]
            if rest in (["show"], ["profiles"], ["validate"]):
                return f"models:{rest[0]}"
            flags = {}
            if rest and rest[0] == "set" and len(rest) == 7:
                pos, fl = rest[1:3], rest[3:]
            elif rest and rest[0] == "use" and len(rest) == 4:
                pos, fl = rest[1:2], rest[2:]
            elif rest and rest[0] == "reset" and len(rest) == 3:
                pos, fl = [], rest[1:]
            else:
                return "models-usage"
            for i in range(0, len(fl), 2):
                if fl[i] in flags or fl[i] not in ("--profile", "--scope"):
                    return "models-usage"
                flags[fl[i]] = fl[i + 1]
            need = {"set": {"--profile", "--scope"}, "use": {"--scope"}, "reset": {"--scope"}}[rest[0]]
            if set(flags) != need or flags["--scope"] not in ("project", "user"):
                return "models-usage"
            if rest[0] == "set" and pos[0] not in self.all_roles + ["all"]:
                return "models-usage"
            return f"models:{rest[0]}"
        if tokens and tokens[0] in ("DudeWhereIsMyArch", "arch", "where"):
            return "arch"
        if tokens and tokens[0] in ("DudeWriteMyFeature", "feature", "write"):
            return "feature"
        return "usage"

    def cmd_set(self, text, role, model_id, profile):
        if role not in self.all_roles + ["all"] or not self.valid_profile_name(profile) or not self.valid_id(model_id):
            return {"status": "rejected"}
        if text is None:
            data = {"schema_version": "1.0", "runtimes": {}}
        else:
            data, errs = self.parse(text)
            if errs:
                return {"status": "refused-invalid-file", "errors": errs}
            data = copy.deepcopy(data)
        ns = data["runtimes"].setdefault(self.bundle, {"active_profile": None, "profiles": {}})
        prof = ns["profiles"].setdefault(profile, {})
        for r in (self.roles if role == "all" else [role]):
            prof[r] = model_id
        out = yaml.safe_dump(data, sort_keys=False)
        assert self.parse(out)[1] == []
        return {"status": "saved-unvalidated", "text": out}

    def cmd_use(self, text, profile):
        data, errs = self.parse(text) if text is not None else ({"schema_version": "1.0", "runtimes": {}}, [])
        if errs:
            return {"status": "refused-invalid-file"}
        data = copy.deepcopy(data)
        ns = data["runtimes"].setdefault(self.bundle, {"active_profile": None, "profiles": {}})
        if profile != "bundled-default":
            prof = ns["profiles"].get(profile)
            if prof is None or set(prof) != set(self.all_roles):
                return {"status": "rejected-incomplete-or-missing"}
        ns["active_profile"] = profile
        return {"status": "selected", "text": yaml.safe_dump(data, sort_keys=False)}

    def cmd_reset(self, text, existing: set[str]):
        if text is None:
            return {"status": "noop"}
        data, errs = self.parse(text)
        if errs:
            n = 1
            while f"models.yaml.invalid-{n}" in existing:
                n += 1
            return {"status": "quarantined", "renamed_to": f"models.yaml.invalid-{n}"}
        data = copy.deepcopy(data)
        data["runtimes"].pop(self.bundle, None)
        if not data["runtimes"]:
            return {"status": "deleted-file"}
        return {"status": "namespace-removed", "text": yaml.safe_dump(data, sort_keys=False)}

    def launch_validate(self, resolved, session):
        """session: model_param bool, accepts(set of ids or None=unknown), tools{role:set}."""
        if resolved["status"] != "ok":
            return {"status": "blocked", "gate": resolved["gate"], "effective": None}
        req = {"dev-dude-orchestrator": {"Skill", "delegate", "write"}, "feature-implementer": {"delegate", "write"},
               "test-implementer": {"write"}, "investigation-documenter": {"write"}}
        for role, need in req.items():
            if not need <= session["tools"].get(role, set()):
                return {"status": "blocked", "gate": "MODEL CAPABILITY GATE", "effective": None}
        accepts = session["accepts"]
        if resolved["profile"] == "bundled-default":
            for role, mid in resolved["models"].items():
                if accepts is not None and mid not in accepts:
                    return {"status": "blocked", "gate": "MODEL CAPABILITY GATE", "effective": None}
            return {"status": "ok", "effective": dict(resolved["models"]), "path": "legacy-frontmatter"}
        if not session["model_param"] or accepts is None:
            return {"status": "blocked", "gate": "MODEL CAPABILITY GATE", "effective": None}
        ids = list(resolved["models"].values()) + [resolved["critique"]]
        if any(mid not in accepts for mid in ids):
            return {"status": "blocked", "gate": "MODEL CAPABILITY GATE", "effective": None}
        return {"status": "ok", "effective": dict(resolved["models"]), "path": "per-dispatch-parameter"}

    @staticmethod
    def critique_model(resolved, verified_stronger):
        if resolved.get("critique"):
            return {"status": "ok", "model": resolved["critique"]}
        if verified_stronger:
            return {"status": "ok", "model": verified_stronger}
        return {"status": "blocked", "gate": "MODEL CAPABILITY GATE"}

    @staticmethod
    def pin(resolved, policy_digest="sha256:" + "0" * 64, version=1):
        text = yaml.safe_dump({"profile": resolved["profile"], "models": resolved["models"],
                               "critique": resolved["critique"], "policy_snapshot_digest": policy_digest,
                               "snapshot_version": version}, sort_keys=True)
        return text, "sha256:" + hashlib.sha256(text.encode()).hexdigest()

    @staticmethod
    def resume(snapshot, digest, policy_digest="sha256:" + "0" * 64):
        """Resume never consults config: missing/mismatched snapshot or a different policy digest blocks."""
        if snapshot is None:
            return {"status": "blocked", "gate": "MODEL PIN GATE"}
        if "sha256:" + hashlib.sha256(snapshot.encode()).hexdigest() != digest:
            return {"status": "blocked", "gate": "MODEL PIN GATE"}
        data = yaml.safe_load(snapshot)
        if data.get("policy_snapshot_digest") != policy_digest:
            return {"status": "blocked", "gate": "MODEL PIN GATE"}
        return {"status": "ok", "models": data["models"]}

    @staticmethod
    def repin(old_snapshot, old_digest, policy_digest, quiescent, decision, validation, new_resolved):
        """models.yaml pinning.repin: explicit approved migration, never a repair of a bad snapshot."""
        cur = ModelPolicy.resume(old_snapshot, old_digest, policy_digest)
        if cur["status"] != "ok" or quiescent is not True or not decision or (validation or {}).get("status") != "ok":
            return {"status": "blocked", "gate": "MODEL PIN GATE"}
        version = yaml.safe_load(old_snapshot)["snapshot_version"] + 1
        text, digest = ModelPolicy.pin(new_resolved, policy_digest, version)
        return {"status": "ok", "snapshot": text, "digest": digest, "kept": (old_snapshot, old_digest),
                "amendment": {"old": old_digest, "new": digest, "decision": decision}}


def policy_snapshot(root: Path, files: list[str]):
    """Reference for manifest.yaml integrity: per-file sha256 over exact bytes, then digest of the snapshot."""
    entries = {rel: "sha256:" + hashlib.sha256((root / rel).read_bytes()).hexdigest() for rel in sorted(files)}
    text = yaml.safe_dump({"schema_version": "1.0", "files": entries}, sort_keys=True)
    return entries, "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def verify_policy(snapshot_entries: dict, files: dict):
    """files: rel -> current bytes (None if missing). Any added/removed/changed file blocks."""
    current = {rel: "sha256:" + hashlib.sha256(b).hexdigest() for rel, b in files.items() if b is not None}
    changed = sorted(set(snapshot_entries) ^ set(current) | {r for r in current if snapshot_entries.get(r) != current[r]})
    return {"status": "blocked", "gate": "POLICY INTEGRITY GATE", "changed": changed} if changed else {"status": "ok"}


def run_scenarios(states: dict) -> tuple[int, int]:
    results = []

    def scenario(name, fn):
        try:
            ok = fn()
        except Exception as exc:  # noqa: BLE001 - report any helper failure as scenario failure
            ok = False
            name += f" (error: {exc})"
        results.append((name, bool(ok)))

    for bundle in ("copilot", "claude"):
        docs = states[bundle]["docs"]
        mp = ModelPolicy(bundle, docs["policies/models.yaml"], docs["policies/commands.yaml"])
        other = "claude" if bundle == "copilot" else "copilot"
        full = {r: "vendor/model-a" for r in mp.roles} | {"critique": "vendor/model-strong"}

        def cfg(ns_self=None, ns_other=None, version="1.0"):
            rts = {}
            if ns_self is not None:
                rts[bundle] = copy.deepcopy(ns_self)
            if ns_other is not None:
                rts[other] = copy.deepcopy(ns_other)
            return yaml.safe_dump({"schema_version": version, "runtimes": rts}, sort_keys=False)

        good = {"active_profile": "team", "profiles": {"team": dict(full)}}
        p = f"[{bundle}] "
        if bundle == "copilot":
            scenario(p + "route `models show`", lambda: mp.route(["models", "show"]) == "models:show")
            scenario(p + "route `models refresh` is architecture refresh", lambda: mp.route(["models", "refresh"]) == "refresh:models")
            scenario(p + "route `feature models cache` is feature input", lambda: mp.route(["feature", "models", "cache"]) == "feature")
            scenario(p + "route models set all with flags in any order",
                     lambda: mp.route(["models", "set", "all", "x/y", "--scope", "user", "--profile", "p"]) == "models:set")
            scenario(p + "unknown models subcommand prints models usage", lambda: mp.route(["models", "bogus"]) == "models-usage")
            scenario(p + "unknown role prints models usage",
                     lambda: mp.route(["models", "set", "nobody", "x", "--profile", "p", "--scope", "user"]) == "models-usage")
            scenario(p + "missing --scope prints models usage",
                     lambda: mp.route(["models", "use", "p", "--profile", "p"]) == "models-usage")
            scenario(p + "duplicate flag prints models usage",
                     lambda: mp.route(["models", "reset", "--scope", "user"]) == "models:reset"
                     and mp.route(["models", "use", "p", "--scope", "user", "--scope", "user"]) == "models-usage")
            scenario(p + "`update refresh` stays refresh; `update x` is usage",
                     lambda: mp.route(["update", "refresh"]) == "refresh:update" and mp.route(["update", "x", "y"]) == "usage")
            scenario(p + "grammar forms match commands.yaml",
                     lambda: len(mp.grammar) == 6 and all(f.startswith("models ") for f in mp.grammar))
        scenario(p + "no config -> bundled-default",
                 lambda: mp.resolve(None, None)["profile"] == "bundled-default" and mp.resolve(None, None)["models"] == mp.default)
        scenario(p + "user active profile used", lambda: mp.resolve(None, cfg(good))["scope"] == "user")
        scenario(p + "project active overrides user",
                 lambda: mp.resolve(cfg({"active_profile": "proj", "profiles": {"proj": dict(full)}}), cfg(good))["profile"] == "proj")
        scenario(p + "inactive project draft does not shadow user",
                 lambda: mp.resolve(cfg({"active_profile": None, "profiles": {"draft": {"critique": "a/b"}}}), cfg(good))["profile"] == "team")
        scenario(p + "project bundled-default shadows user",
                 lambda: mp.resolve(cfg({"active_profile": "bundled-default", "profiles": {}}), cfg(good))["profile"] == "bundled-default")
        scenario(p + "other runtime namespace does not affect resolution",
                 lambda: mp.resolve(cfg(None, good), None)["profile"] == "bundled-default")
        scenario(p + "unknown top-level key blocks launch",
                 lambda: mp.resolve(None, cfg(good) + "extra: 1\n")["gate"] == "MODEL CONFIG GATE")
        scenario(p + "unknown schema version blocks", lambda: mp.resolve(cfg(good, version="2.0"), None)["status"] == "blocked")
        scenario(p + "wrong type for active_profile blocks",
                 lambda: mp.resolve(cfg({"active_profile": 3, "profiles": {}}), None)["status"] == "blocked")
        scenario(p + "duplicate key rejected",
                 lambda: mp.parse("schema_version: '1.0'\nschema_version: '1.0'\nruntimes: {}\n")[1] != [])
        scenario(p + "anchors rejected",
                 lambda: mp.parse("schema_version: '1.0'\nruntimes: &a {}\n")[1] != [])
        scenario(p + "explicit tags and multiple documents rejected",
                 lambda: mp.parse("schema_version: !!str 1.0\nruntimes: {}\n")[1] != []
                 and mp.parse("schema_version: '1.0'\nruntimes: {}\n---\n{}\n")[1] != [])
        scenario(p + "oversized file rejected", lambda: mp.parse("#" * (mp.max_bytes + 1))[1] != [])
        scenario(p + "alias model IDs rejected in config",
                 lambda: mp.parse(cfg({"active_profile": None, "profiles": {"x": {"critique": "opus"}}}))[1] != [])
        scenario(p + "URL and dot-dot model IDs rejected",
                 lambda: not mp.valid_id("https://x") and not mp.valid_id("a/../b") and mp.valid_id("qwen2.5-coder:32b"))
        scenario(p + "reasoning keys rejected",
                 lambda: mp.parse(cfg({"active_profile": None, "profiles": {"x": {"reasoning_effort": "high"}}}))[1] != [])
        scenario(p + "active profile missing a role blocks",
                 lambda: mp.resolve(cfg({"active_profile": "t", "profiles": {"t": {k: v for k, v in full.items() if k != mp.roles[0]}}}), None)["status"] == "blocked")
        scenario(p + "custom profile without critique blocks",
                 lambda: mp.resolve(cfg({"active_profile": "t", "profiles": {"t": {r: "a/b" for r in mp.roles}}}), None)["status"] == "blocked")
        scenario(p + "reserved profile name rejected by set", lambda: mp.cmd_set(None, "critique", "a/b", "bundled-default")["status"] == "rejected")

        def set_keeps_draft_and_namespace():
            res = mp.cmd_set(cfg({"active_profile": None, "profiles": {}}, good), "all", "local/qwen", "draft")
            data = yaml.safe_load(res["text"])
            return (res["status"] == "saved-unvalidated" and data["runtimes"][bundle]["active_profile"] is None
                    and data["runtimes"][other] == good and "critique" not in data["runtimes"][bundle]["profiles"]["draft"])
        scenario(p + "set saves unvalidated draft, keeps active and other namespace", set_keeps_draft_and_namespace)
        scenario(p + "set refuses invalid existing file", lambda: mp.cmd_set("runtimes: [\n", "critique", "a/b", "p")["status"] == "refused-invalid-file")

        def use_rules():
            draft = cfg({"active_profile": None, "profiles": {"d": {"critique": "a/b"}, "full": dict(full)}})
            return (mp.cmd_use(draft, "d")["status"] == "rejected-incomplete-or-missing"
                    and mp.cmd_use(draft, "missing")["status"] == "rejected-incomplete-or-missing"
                    and yaml.safe_load(mp.cmd_use(draft, "full")["text"])["runtimes"][bundle]["active_profile"] == "full"
                    and mp.cmd_use(None, "bundled-default")["status"] == "selected")
        scenario(p + "use requires an existing complete profile or bundled-default", use_rules)

        def reset_rules():
            both = mp.cmd_reset(cfg(good, good), set())
            only = mp.cmd_reset(cfg(good), set())
            bad = mp.cmd_reset("schema_version: '1.0'\nruntimes: {x: 1}\n", {"models.yaml.invalid-1"})
            return (both["status"] == "namespace-removed" and bundle not in yaml.safe_load(both["text"])["runtimes"]
                    and yaml.safe_load(both["text"])["runtimes"][other] == good
                    and only["status"] == "deleted-file" and bad == {"status": "quarantined", "renamed_to": "models.yaml.invalid-2"}
                    and mp.cmd_reset(None, set())["status"] == "noop")
        scenario(p + "reset removes only own namespace, quarantines malformed, no-op when absent", reset_rules)
        tools = {"dev-dude-orchestrator": {"Skill", "delegate", "write"}, "feature-implementer": {"delegate", "write"},
                 "test-implementer": {"write"}, "investigation-documenter": {"write"}}
        custom = mp.resolve(cfg(good), None)
        scenario(p + "custom profile without per-dispatch model parameter blocks, no fallback",
                 lambda: mp.launch_validate(custom, {"model_param": False, "accepts": None, "tools": tools}) ==
                 {"status": "blocked", "gate": "MODEL CAPABILITY GATE", "effective": None})
        scenario(p + "custom profile with unexposed (e.g. cloud-only vs local) ID blocks",
                 lambda: mp.launch_validate(custom, {"model_param": True, "accepts": {"vendor/model-a"}, "tools": tools})["status"] == "blocked")
        scenario(p + "custom profile accepted only when every exact ID is exposed",
                 lambda: mp.launch_validate(custom, {"model_param": True, "accepts": {"vendor/model-a", "vendor/model-strong"},
                                                     "tools": tools})["effective"] == custom["models"])
        scenario(p + "missing required delegation tools blocks",
                 lambda: mp.launch_validate(custom, {"model_param": True, "accepts": {"vendor/model-a", "vendor/model-strong"},
                                                     "tools": {}})["gate"] == "MODEL CAPABILITY GATE")
        default = mp.resolve(None, None)
        scenario(p + "bundled-default keeps frontmatter values unchanged (aliases not normalized)",
                 lambda: mp.launch_validate(default, {"model_param": False, "accepts": None, "tools": tools})["effective"] == mp.default)
        scenario(p + "bundled-default rejected by runtime gates, no substitution",
                 lambda: mp.launch_validate(default, {"model_param": True, "accepts": set(), "tools": tools})["status"] == "blocked")
        scenario(p + "critique null requires verified stronger model",
                 lambda: mp.critique_model(default, None)["status"] == "blocked"
                 and mp.critique_model(default, "verified/strong")["model"] == "verified/strong")
        scenario(p + "custom critique role is used", lambda: mp.critique_model(custom, None)["model"] == "vendor/model-strong")

        def pin_rules():
            snap, digest = mp.pin(custom)
            later = mp.resolve(None, None)  # config changed after pinning
            return (mp.resume(snap, digest)["models"] == custom["models"] and later["profile"] == "bundled-default"
                    and mp.resume(snap + "x", digest)["gate"] == "MODEL PIN GATE"
                    and mp.resume(None, digest)["gate"] == "MODEL PIN GATE")
        scenario(p + "pinned snapshot governs resume; mismatch or missing blocks", pin_rules)

        root = BUNDLES[bundle]
        mfiles = list(states[bundle]["manifest"]["files"]) + ["policies/manifest.yaml"]
        entries, pdigest = policy_snapshot(root, mfiles)
        live = {rel: (root / rel).read_bytes() for rel in mfiles}

        def policy_edit_blocks():
            edited = dict(live)
            edited["policies/state.yaml"] = live["policies/state.yaml"] + b"# edited mid-run\n"
            missing = dict(live)
            missing["policies/handoff.yaml"] = None
            added = dict(live) | {"policies/agents/extra.yaml": b"x: 1\n"}
            return (verify_policy(entries, live)["status"] == "ok"
                    and verify_policy(entries, edited)["changed"] == ["policies/state.yaml"]
                    and verify_policy(entries, missing)["gate"] == "POLICY INTEGRITY GATE"
                    and verify_policy(entries, added)["changed"] == ["policies/agents/extra.yaml"])
        scenario(p + "mid-run edit/removal/addition of any policy file blocks resume (POLICY INTEGRITY GATE)",
                 policy_edit_blocks)
        scenario(p + "manifest digest alone misses a non-manifest policy edit; policy snapshot catches it",
                 lambda: entries["policies/manifest.yaml"] == "sha256:" + hashlib.sha256(live["policies/manifest.yaml"]).hexdigest()
                 and verify_policy(entries, dict(live) | {"policies/models.yaml": live["policies/models.yaml"] + b" "})["status"] == "blocked")

        def model_snapshot_policy_digest():
            snap, digest = mp.pin(custom, pdigest)
            other = "sha256:" + "f" * 64
            return (mp.resume(snap, digest, pdigest)["status"] == "ok"
                    and mp.resume(snap, digest, other)["gate"] == "MODEL PIN GATE")
        scenario(p + "model snapshot validated under another policy snapshot blocks resume", model_snapshot_policy_digest)

        def repin_rules():
            snap, digest = mp.pin(custom, pdigest)
            ok_val = mp.launch_validate(custom, {"model_param": True, "accepts": {"vendor/model-a", "vendor/model-strong"},
                                                "tools": tools})
            done = mp.repin(snap, digest, pdigest, True, '"switch to team2"', ok_val, custom)
            return (done["status"] == "ok" and yaml.safe_load(done["snapshot"])["snapshot_version"] == 2
                    and done["kept"] == (snap, digest)
                    and mp.repin(snap, digest, pdigest, False, '"go"', ok_val, custom)["status"] == "blocked"
                    and mp.repin(snap, digest, pdigest, None, '"go"', ok_val, custom)["status"] == "blocked"
                    and mp.repin(snap, digest, pdigest, True, "", ok_val, custom)["status"] == "blocked"
                    and mp.repin(snap, digest, pdigest, True, '"go"', {"status": "blocked"}, custom)["status"] == "blocked"
                    and mp.repin(snap + "x", digest, pdigest, True, '"go"', ok_val, custom)["status"] == "blocked"
                    and mp.repin(None, digest, pdigest, True, '"go"', ok_val, custom)["status"] == "blocked")
        scenario(p + "re-pin needs quiescence, quoted decision, validation; never repairs a bad snapshot", repin_rules)
    passed = sum(ok for _, ok in results)
    for name, ok in results:
        if not ok:
            fail(f"scenario failed: {name}")
    return len(results), passed


def main() -> int:
    inv, record = load_inventory()
    counts: dict = {}
    states = {}
    closure_refs = parity_checks = 0
    for bundle in BUNDLES:
        state = audit_bundle(bundle, inv, record, counts)
        if not state:
            continue
        states[bundle] = state
        state["conflict_ids"] = set(record["conflict_decisions"])
        audit_load_sets(bundle, state, inv)
        closure_refs += audit_load_set_closure(bundle, state)
        audit_integrity(bundle, state)
        parity_checks += audit_reference_parity(bundle, state)
        audit_frontmatter(bundle, state)
    if len(states) == 2:
        wf_checks = audit_bump_workflow()
        audit_workflow_and_links(states)
        audit_record(inv, record, counts)
        recon = audit_reconciliation(record, states)
        total, passed = run_scenarios(states)
    else:
        total = passed = wf_checks = 0
        recon = {}
    base_rules = sum(len(p["rules"]) for p in inv["policies"])
    print(f"baseline: {len(inv['policies'])} policies, {base_rules} rules")
    for bundle in BUNDLES:
        c = counts.get(bundle, {})
        print(f"{bundle}: {c.get('policies')} policies, {c.get('rules')} rules in YAML; "
              f"source_nuance verified against baseline blobs for {c.get('nuance_checked')} policies "
              f"({c.get('nuance_unavailable')} unverifiable: baseline blob unavailable)")
    print(f"distinct rule IDs in YAML: {len(counts.get('rule_ids', ()))} "
          f"({len(record['added_rules'])} added, {len(record['rule_amendments'])} amended; reconciled with YAML: "
          f"{recon.get('added')} added_by, {recon.get('amended')} amendment blocks)")
    print(f"scenarios: {passed}/{total} passed (pure helpers; not host execution)")
    print(f"load-set closure: {closure_refs} policy/file references checked; "
          f"YAML-vs-reference-model parity: {parity_checks} checks")
    print(f"bump workflow: {wf_checks} trigger/filter/bump/loop checks against the embedded script")
    print("independent semantic review: pending")
    if failures:
        print(f"\nFAIL: {len(failures)} issue(s)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nPASS: repository consistency checks passed (not proof of runtime behaviour)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
