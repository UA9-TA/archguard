# ArchGuard

![PyPI](https://img.shields.io/pypi/v/archguard)
![License](https://img.shields.io/github/license/UA9-TA/archguard)
![Build](https://img.shields.io/github/actions/workflow/status/UA9-TA/archguard/ci.yml)

*Code review catches file-level bugs. ArchGuard catches architecture-level bugs.*

ArchGuard is an open-source CLI tool that enforces service architecture rules across repositories. It catches circular dependencies, API contract violations, and service boundary breaches in microservice codebases before they merge — the class of bugs no linter or code review tool currently catches.

## The problem
Code review tools check individual files. They cannot see that Service A now imports from Service B which imports from Service A (circular dependency), or that Service A changed its response schema in a way that breaks Service C's consumer. These cross-service bugs only appear in integration environments — expensive, slow, and embarrassing. ArchGuard makes architecture rules explicit in a YAML file and validates every commit/PR against them automatically.

## Demo
<!-- Add demo.gif here -->

## Install

```bash
pip install archguard
```

## Quick start

```bash
# Initialize architecture schema for current repo
archguard init

# Edit .archguard.yml

# Validate current codebase against schema
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

## Sample output

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

| Violation Type | Detected? |
| --- | --- |
| Circular Dependencies | ✅ |
| API Contract Breaches | ✅ |
| Boundary Violations (Internal imports) | ✅ |

## CI integration

Add ArchGuard to your GitHub Actions:

```yaml
name: ArchGuard
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install archguard
      - run: archguard check
```

## Pre-commit hook

```bash
archguard install-hook
```

## Contributing / License
MIT License. Pull requests are welcome!
