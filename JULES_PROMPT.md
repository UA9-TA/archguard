# Jules Build Prompt — ArchGuard v1.0

## What You Are Building

**ArchGuard** is an open-source CLI tool that enforces service architecture rules across repositories. It catches circular dependencies, API contract violations, and service boundary breaches in microservice codebases before they merge — the class of bugs no linter or code review tool currently catches.

The core problem: Code review tools (GitHub, Reviewdog, CodeRabbit) check individual files. They cannot see that Service A now imports from Service B which imports from Service A (circular dependency), or that Service A changed its response schema in a way that breaks Service C's consumer. These cross-service bugs only appear in integration environments — expensive, slow, and embarrassing. ArchGuard makes architecture rules explicit in a YAML file and validates every commit/PR against them automatically.

**Target:** Top GitHub trending. Platform engineering and microservices teams have no OSS solution for this today.

---

## Core User Flow

```bash
# Install
pip install archguard

# Initialize architecture schema for current repo
archguard init

# Validate current codebase against schema
archguard check

# Validate a specific PR (fetches diff from GitHub)
archguard check --pr 42

# Watch mode — re-validate on file changes
archguard watch

# Visualize dependency graph
archguard graph

# Install as pre-commit hook
archguard install-hook
```

**Output:**
```
ArchGuard — Architecture Validation
──────────────────────────────────────────────────
✦ Schema loaded       .archguard.yml (8 services, 14 rules)
✦ Files checked       23 changed files

  ── VIOLATION: Circular Dependency ───────────────
  auth-service  →  user-service  →  auth-service
  Introduced by: auth/clients/user_client.py:12
    from user_service.auth import verify_token  ← creates cycle

  ── VIOLATION: Contract Breach ────────────────────
  payment-service exposes: POST /api/charge
  Changed: response.transaction_id (str) → response.txn (str)
  Consumers expecting transaction_id: order-service, webhook-service

  ── VIOLATION: Boundary Breach ────────────────────
  notification-service imports from payment-service internals
  notification/sender.py:8
    from payment.models import PaymentRecord  ← internal model
  Rule: notification-service may only consume payment-service PUBLIC API

✦ 3 violations found — merge blocked
──────────────────────────────────────────────────
```

---

## Tech Stack

- **Language:** Python 3.10+
- **CLI framework:** Typer + Rich
- **AI:** Anthropic Claude API (`claude-sonnet-4-6`) — for explaining violations in plain English
- **Schema format:** YAML (`.archguard.yml` in project root)
- **Import analysis:** Python `ast` module for import graph extraction
- **API contract parsing:** OpenAPI/JSON schema diffing with `jsonschema`
- **Git integration:** `subprocess` + `git diff`
- **Graph:** `networkx` for circular dependency detection
- **Packaging:** `pyproject.toml` (hatchling), entry point `archguard`

---

## Project Structure

```
archguard/
├── archguard/
│   ├── __init__.py
│   ├── cli.py              # Typer app — check, init, watch, graph, install-hook
│   ├── schema.py           # Loads + validates .archguard.yml
│   ├── import_scanner.py   # AST-based import graph builder
│   ├── cycle_detector.py   # networkx-based circular dependency detection
│   ├── contract_checker.py # OpenAPI/schema diff — detects breaking changes
│   ├── boundary_checker.py # Validates imports don't cross service boundaries
│   ├── explainer.py        # Claude API — explains violations in plain English
│   ├── display.py          # Rich terminal output
│   └── config.py           # Config reader
├── tests/
│   ├── test_import_scanner.py
│   ├── test_cycle_detector.py
│   ├── test_boundary_checker.py
│   ├── test_contract_checker.py
│   └── fixtures/
│       ├── sample_arch/          # Small fake microservice layout
│       │   ├── auth_service/
│       │   ├── user_service/
│       │   ├── payment_service/
│       │   └── notification_service/
│       ├── .archguard.yml        # Schema defining rules for sample_arch
│       └── breaking_diff.patch   # Diff introducing all 3 violation types
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
└── README.md
```

---

## Detailed Module Specs

### `.archguard.yml` Schema Format
```yaml
version: 1

services:
  - name: auth-service
    path: auth/
    public_api:
      - path: /api/auth/*
        schema: auth/openapi.yml
    may_import_from: []          # auth-service imports from nobody

  - name: user-service
    path: user/
    public_api:
      - path: /api/users/*
        schema: user/openapi.yml
    may_import_from:
      - auth-service             # user-service may import auth-service's PUBLIC exports

  - name: payment-service
    path: payment/
    public_api:
      - path: /api/charge
        schema: payment/openapi.yml
    may_import_from:
      - user-service

  - name: notification-service
    path: notification/
    may_import_from:
      - user-service             # only public API, not internals

rules:
  - no_circular_dependencies: true
  - enforce_public_api_contracts: true
  - no_internal_imports: true    # services may not import from another service's non-public paths
```

### `schema.py` — Schema loading
- Load `.archguard.yml` with `PyYAML`
- Validate schema structure (required fields, valid service references)
- Return typed `ArchSchema` dataclass

### `import_scanner.py` — Import graph
- For each Python file in each service path: use `ast.parse()` to extract all imports
- Map each import to a service (by matching import path prefix to `service.path`)
- Return `ImportGraph`: `{service_name: {imports_from: set[service_name]}}`

### `cycle_detector.py` — Circular dependency detection
- Build `networkx.DiGraph` from `ImportGraph`
- Use `networkx.find_cycle()` to detect cycles
- Return list of `Cycle` dataclasses: `{services: list[str], introduced_by: file_path, line: int}`

### `boundary_checker.py` — Boundary enforcement
- For each import from Service B into Service A: check if the imported path is within `service_b.public_api` paths
- If importing from `payment/models.py` but `payment-service` public paths are only `payment/api/` → violation
- Return list of `BoundaryViolation` dataclasses

### `contract_checker.py` — API contract validation
- Load OpenAPI schemas for services that have them
- Compare old schema (from git HEAD) vs new schema (current)
- Detect breaking changes: removed fields, type changes, renamed fields
- Flag which other services consume the changed endpoint (from `may_import_from` declarations)

### `explainer.py` — Claude API
Only called when user runs `archguard check --explain` or `archguard explain <violation>`.
Sends the violation details + surrounding code + schema rules to Claude.
Returns a plain-English explanation of why it's a violation and the recommended fix.

---

## README Spec

1. **Hero** — badges + one-liner: *"Code review catches file-level bugs. ArchGuard catches architecture-level bugs."*
2. **The problem** — circular dependency example: auth imports user imports auth — nobody notices until integration tests
3. **Demo** — `<!-- Add demo.gif here -->`
4. **Install** — `pip install archguard`
5. **Quick start** — `archguard init` → edit `.archguard.yml` → `archguard check`
6. **Sample `.archguard.yml`** — the exact schema format above
7. **Sample output** — exact Rich output from above
8. **What it detects** — table: circular deps ✅, contract breaches ✅, boundary violations ✅
9. **CI integration** — GitHub Actions example
10. **Pre-commit hook** — `archguard install-hook`
11. **Contributing / License**

---

## `pyproject.toml`

```toml
[project]
name = "archguard"
version = "0.1.0"
description = "Enforce microservice architecture rules across repos — catch circular deps and contract violations before merge"
authors = [{name = "UA9-TA", email = "vkrmsatsangi@gmail.com"}]
keywords = ["microservices", "architecture", "cli", "developer-tools", "devops", "platform-engineering"]
dependencies = [
    "typer>=0.12", "rich>=13", "anthropic>=0.25",
    "pyyaml>=6.0", "networkx>=3.0", "jsonschema>=4.0",
    "tomli>=2.0; python_version < '3.11'",
]
[project.optional-dependencies]
dev = ["pytest", "ruff", "pytest-mock", "pytest-cov"]
[project.scripts]
archguard = "archguard.cli:app"
[project.urls]
Homepage = "https://github.com/UA9-TA/archguard"
Changelog = "https://github.com/UA9-TA/archguard/blob/main/CHANGELOG.md"
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--ignore=tests/fixtures"
[tool.ruff]
line-length = 100
target-version = "py310"
[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]
```

---

## Fixtures

### `tests/fixtures/sample_arch/`
Four small Python service directories, each with 2-3 files:
- `auth_service/` — has `api.py` and `clients/user_client.py` (imports from user_service creating cycle)
- `user_service/` — has `api.py` and `auth/verify.py` (imports from auth_service)
- `payment_service/` — has `api.py` and `models.py` (internal model)
- `notification_service/` — has `sender.py` (incorrectly imports `payment_service/models.py`)

### `tests/fixtures/.archguard.yml`
Schema defining all 4 services with rules that the sample_arch violates in 3 ways.

---

## Definition of Done

- [ ] `archguard init` generates a valid `.archguard.yml` template
- [ ] `archguard check` detects circular dep in fixture sample_arch
- [ ] `archguard check` detects boundary violation in fixture sample_arch
- [ ] `archguard graph` prints ASCII dependency graph
- [ ] `archguard install-hook` writes working pre-commit hook
- [ ] CI passes on Python 3.10, 3.11, 3.12
- [ ] ruff passes


## The Developer Toolkit Ecosystem

This tool is part of a suite of open-source AI-powered developer tools built by the same team:

| Tool | What it does |
|---|---|
| **[RootCause](https://github.com/UA9-TA/rootcause)** | Auto-diagnose failing tests — AI root cause + fix |
| **[ErrorMentor](https://github.com/UA9-TA/errormentor)** | Auto-diagnose production errors — correlate logs with git commits |
| **[TestGap](https://github.com/UA9-TA/testgap)** | Find untested code paths after every commit |
| **[HalluCheck](https://github.com/UA9-TA/hallucheck)** | Catch AI hallucinations in code diffs |
| **[IntentDiff](https://github.com/UA9-TA/intentdiff)** | Understand what a diff *actually* does semantically |
| **[DepSecure](https://github.com/UA9-TA/depsecure)** | Block vulnerable dependencies at commit time |
| **[ArchGuard](https://github.com/UA9-TA/archguard)** | Enforce microservice architecture rules across repos |
| **[SpendSentry](https://github.com/UA9-TA/spendsentry)** | Monitor cloud spend in real time — alert before costs spiral |
| **[ContextKit](https://github.com/UA9-TA/contextkit)** | Build minimal AI context bundles — 88% fewer tokens |

## Repo Details
- GitHub: https://github.com/UA9-TA/archguard
- Local path: /Users/chitra/Documents/Projects/archguard
- Branch: main — License: MIT
