# ArchGuard

![PyPI - Version](https://img.shields.io/pypi/v/archguard)
![Python Versions](https://img.shields.io/pypi/pyversions/archguard)
![License](https://img.shields.io/github/license/UA9-TA/archguard)

*Code review catches file-level bugs. ArchGuard catches architecture-level bugs.*

**ArchGuard** is an open-source CLI tool that enforces service architecture rules across repositories. It catches circular dependencies, API contract violations, and service boundary breaches in microservice codebases before they merge — the class of bugs no linter or code review tool currently catches.

## The Problem

Code review tools check individual files. They cannot see that `Service A` now imports from `Service B` which imports from `Service A` (circular dependency), or that `Service A` changed its response schema in a way that breaks `Service C`'s consumer. These cross-service bugs only appear in integration environments — expensive, slow, and embarrassing.

ArchGuard makes architecture rules explicit in a YAML file and validates every commit/PR against them automatically.

## Demo

<!-- Add demo.gif here -->

## Install

```bash
pip install archguard
```

## Quick Start

1. Initialize the schema:
```bash
archguard init
```

2. Edit `.archguard.yml` to define your services and rules.

3. Check your codebase:
```bash
archguard check
```

## Sample `.archguard.yml`

```yaml
version: 1

services:
  - name: auth-service
    path: auth/
    public_api:
      - path: /api/auth/*
        schema: auth/openapi.yml
    may_import_from: []

  - name: user-service
    path: user/
    public_api:
      - path: /api/users/*
        schema: user/openapi.yml
    may_import_from:
      - auth-service

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
      - user-service

rules:
  - no_circular_dependencies: true
  - enforce_public_api_contracts: true
  - no_internal_imports: true
```

## Sample Output

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

## What it detects

| Violation | Status | Description |
|---|---|---|
| Circular Dependencies | ✅ | Prevents deadlocks and deep coupling by catching `A -> B -> A`. |
| Boundary Breaches | ✅ | Ensures services only consume public APIs of other services, not internals. |
| Contract Breaches | ✅ | Detects breaking API schema changes that break downstream consumers. |

## CI Integration

Integrate ArchGuard easily in your GitHub Actions workflow:

```yaml
name: ArchGuard Validation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install ArchGuard
        run: pip install archguard
      - name: Run ArchGuard Check
        run: archguard check
```

## Pre-commit Hook

Install ArchGuard as a pre-commit hook to catch violations locally before even committing:

```bash
archguard install-hook
```

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

## Contributing / License

Contributions are welcome! Open an issue or submit a PR.

License: MIT
