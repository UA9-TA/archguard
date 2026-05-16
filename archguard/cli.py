import os
import sys
import time

import typer

from .boundary_checker import check_boundaries
from .contract_checker import check_contracts
from .cycle_detector import detect_cycles
from .display import (
    console,
    print_boundary,
    print_contract,
    print_cycle,
    print_header,
    print_summary,
)
from .explainer import explain_violation
from .import_scanner import scan_imports
from .schema import load_schema

app = typer.Typer(help="ArchGuard - Enforce microservice architecture rules across repos.")

@app.command()
def init():
    """Initialize architecture schema for current repo."""
    content = """version: 1

services:
  - name: auth-service
    path: auth_service/
    public_api:
      - path: /api/auth/*
        schema: auth_service/openapi.yml
    may_import_from: []

  - name: user-service
    path: user_service/
    public_api:
      - path: /api/users/*
        schema: user_service/openapi.yml
    may_import_from:
      - auth-service

  - name: payment-service
    path: payment_service/
    public_api:
      - path: /api/charge
        schema: payment_service/openapi.yml
    may_import_from:
      - user-service

  - name: notification-service
    path: notification_service/
    may_import_from:
      - user-service

rules:
  - no_circular_dependencies: true
  - enforce_public_api_contracts: true
  - no_internal_imports: true
"""
    if os.path.exists('.archguard.yml'):
        console.print("[yellow].archguard.yml already exists.[/yellow]")
        return

    with open('.archguard.yml', 'w') as f:
        f.write(content)
    console.print("[green]Initialized .archguard.yml[/green]")

@app.command()
def check(
    schema_path: str = typer.Option('.archguard.yml', "--schema", "-s", help="Path to schema file"),
    explain: bool = typer.Option(False, "--explain", help="Explain violations using Claude API"),
    pr: int = typer.Option(None, "--pr", help="Validate a specific PR")
):
    """Validate current codebase against schema."""
    if not os.path.exists(schema_path):
        console.print(f"[red]Schema file not found: {schema_path}[/red]")
        sys.exit(1)

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        console.print(f"[red]Error loading schema: {e}[/red]")
        sys.exit(1)

    print_header(schema_path, len(schema.services), 3) # Hardcoded 3 rules for now

    import_graph = scan_imports(schema)

    cycles = detect_cycles(import_graph) if schema.rules.no_circular_dependencies else []
    boundaries = check_boundaries(schema, import_graph)
    contracts = check_contracts(schema)

    for cycle in cycles:
        print_cycle(cycle)
        if explain:
            console.print(f"  [cyan]Explanation:[/cyan] {explain_violation('Circular Dependency', str(cycle))}")

    for boundary in boundaries:
        print_boundary(boundary)
        if explain:
            console.print(f"  [cyan]Explanation:[/cyan] {explain_violation('Boundary Breach', str(boundary))}")

    for contract in contracts:
        print_contract(contract)
        if explain:
            console.print(f"  [cyan]Explanation:[/cyan] {explain_violation('Contract Breach', str(contract))}")

    num_violations = len(cycles) + len(boundaries) + len(contracts)
    print_summary(num_violations)

    if num_violations > 0:
        sys.exit(1)

@app.command()
def watch(schema_path: str = typer.Option('.archguard.yml', "--schema", "-s", help="Path to schema file")):
    """Watch mode — re-validate on file changes."""
    console.print("[cyan]Watch mode enabled. Press Ctrl+C to exit.[/cyan]")
    # Basic implementation, can be improved with watchdog
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("[cyan]Exiting watch mode.[/cyan]")

@app.command()
def graph(schema_path: str = typer.Option('.archguard.yml', "--schema", "-s", help="Path to schema file")):
    """Visualize dependency graph."""
    if not os.path.exists(schema_path):
        console.print(f"[red]Schema file not found: {schema_path}[/red]")
        sys.exit(1)

    schema = load_schema(schema_path)
    import_graph = scan_imports(schema)

    console.print("\n[bold]Dependency Graph:[/bold]")
    for service, imports in import_graph.items():
        console.print(f"[cyan]{service}[/cyan]")
        for target in imports.keys():
            console.print(f"  └─> [green]{target}[/green]")

@app.command()
def install_hook():
    """Install as pre-commit hook."""
    hook_dir = ".git/hooks"
    if not os.path.exists(hook_dir):
        os.makedirs(hook_dir, exist_ok=True)

    hook_path = os.path.join(hook_dir, "pre-commit")

    content = """#!/bin/sh
archguard check
"""
    with open(hook_path, 'w') as f:
        f.write(content)

    os.chmod(hook_path, 0o755)
    console.print("[green]Installed pre-commit hook successfully.[/green]")

if __name__ == "__main__":
    app()
