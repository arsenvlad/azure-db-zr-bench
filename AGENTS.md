# AGENTS.md — Working on azure-db-zr-bench

This repository is designed to be worked on by both humans and coding agents.
Agents modifying or extending this repo **must follow the intent and constraints defined here**.

This file is authoritative for *how* to work in this repo.  
For *what* to build, see: `docs/agent-brief/v1-initial-build.md`.

---

## Project intent (read this first)

`azure-db-zr-bench` exists to measure **relative write-performance impact** of enabling
Zone Redundancy / cross-zone HA in Azure managed databases.

Key principles:
- Comparisons matter more than absolute numbers
- Repeatability matters more than sophistication
- Simplicity matters more than feature completeness

This is **not** a production-grade benchmarking framework.

---

## Scope boundaries (do not cross without justification)

Allowed in v1:
- Simple Python CLI
- Explicit configuration via files
- Write-heavy OLTP-style workloads
- Static HTML or Markdown reports
- Test-only infrastructure assumptions

Out of scope for v1:
- Auto-discovery of Azure resources
- Long-running services or daemons
- Web backends, APIs, or dashboards
- Complex orchestration frameworks
- Read-heavy or mixed workloads unless explicitly requested
- “Smart” tuning logic per database engine

If you think something should cross these boundaries, **document why** before implementing.

---

## Configuration philosophy

- **Config-first, not discovery-first**
- Targets are defined in config files (YAML/JSON), not inferred from Azure
- Secrets are never hardcoded; environment variable overrides are required
- Defaults should be reasonable, visible, and documented

Agents must not add hidden behavior based on environment or heuristics.

---

## Benchmarking philosophy

- Focus on **writes**
- Keep transaction semantics explicit and consistent across DB engines
- Prefer clarity over engine-specific optimizations
- Warm-up must be clearly separated from measured results
- Fail fast on errors; record and surface them

Do not attempt to “optimize away” differences — differences are the point.

---

## Code style expectations

- Readable, boring Python is preferred
- Avoid metaprogramming and excessive abstraction
- Favor explicit loops and clear control flow
- Shared logic belongs in common modules; DB-specific logic belongs in providers
- One obvious way to run a benchmark

If code feels clever, it’s probably wrong for this repo.

---

## Output and results guarantees

Every benchmark run must:
- Produce machine-readable output (`result.json`, `summary.json`)
- Include enough metadata to reproduce the run
- Clearly label service, mode (non-HA / same-zone HA / cross-zone HA / ZR), and timestamp
- Never silently overwrite previous results

Results should be comparable across runs without manual interpretation.

---

## Infrastructure expectations (Bicep)

- Infrastructure is test-only and cost-aware
- Naming must clearly encode service and HA/ZR mode
- Region should be parameterized (default: centralus)
- Networking should be simple and documented, not production-hardened
- Assume infra is disposable

Do not add complexity “just in case”.

---

## Documentation rules

- README commands must work exactly as written
- Examples must be runnable without modification
- If behavior changes, update docs in the same change
- Keep README short; deeper explanations if any a really required belong in `docs/`

---

## Decision tracking

Non-trivial changes should be accompanied by:
- An update to an existing ADR (architecture decision record), or
- A new ADR under `docs/adr/`

This prevents intent drift over time.

---

## Final rule

When in doubt, ask:
> “Does this make the comparison clearer and more repeatable?”

If the answer is no, don’t add it.
