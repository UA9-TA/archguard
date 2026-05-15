import os
import time
from pathlib import Path

import typer
from rich.console import Console

from .boundary_checker import check_boundaries
from .contract_checker import check_contracts
from .cycle_detector import detect_cycles
from .display import (
    print_boundary_violation,
    print_contract_breach,
    print_cycle,
    print_header,
    print_summary,
)
from .explainer import explain_violation
from .import_scanner import scan_imports
from .schema import ArchSchema

app = typer.Typer(help="ArchGuard — Enforce microservice architecture rules")
console = Console()

SCHEMA_FILE = ".archguard.yml"

@app.command()
def init():
    """Initialize a new .archguard.yml schema file in the current directory."""
    if Path(SCHEMA_FILE).exists():
        console.print(f"[red]Error: {SCHEMA_FILE} already exists.[/red]")
        raise typer.Exit(1)

    template = """version: 1

services:
  - name: my-service
    path: src/my_service/
    public_api: []
    may_import_from: []

rules:
  - no_circular_dependencies: true
  - enforce_public_api_contracts: true
  - no_internal_imports: true
"""
    with open(SCHEMA_FILE, "w") as f:
        f.write(template)

    console.print(f"[green]Successfully created {SCHEMA_FILE}[/green]")

def _run_checks(explain: bool = False):
    if not Path(SCHEMA_FILE).exists():
        console.print(f"[red]Error: {SCHEMA_FILE} not found. Run 'archguard init' first.[/red]")
        raise typer.Exit(1)

    try:
        schema = ArchSchema.load(SCHEMA_FILE)
    except Exception as e:
        console.print(f"[red]Failed to load schema: {e}[/red]")
        raise typer.Exit(1)

    num_rules = sum([
        schema.rules.no_circular_dependencies,
        schema.rules.enforce_public_api_contracts,
        schema.rules.no_internal_imports
    ])

    print_header(SCHEMA_FILE, len(schema.services), num_rules)

    # To correctly support checking in the current directory or specified repo
    graph = scan_imports(".", schema)

    violations = []

    if schema.rules.no_circular_dependencies:
        cycles = detect_cycles(graph)
        for cycle in cycles:
            violations.append(("cycle", cycle))

    if schema.rules.no_internal_imports:
        boundaries = check_boundaries(graph, schema)
        for boundary in boundaries:
            violations.append(("boundary", boundary))

    if schema.rules.enforce_public_api_contracts:
        contracts = check_contracts(schema)
        for contract in contracts:
            violations.append(("contract", contract))

    for v_type, violation in violations:
        if v_type == "cycle":
            print_cycle(violation)
            if explain:
                console.print(f"[dim]{explain_violation('Circular Dependency', ' -> '.join(violation.services))}[/dim]\n")
        elif v_type == "boundary":
            print_boundary_violation(violation)
            if explain:
                console.print(f"[dim]{explain_violation('Boundary Breach', violation.rule_broken)}[/dim]\n")
        elif v_type == "contract":
            print_contract_breach(violation)
            if explain:
                console.print(f"[dim]{explain_violation('Contract Breach', violation.description)}[/dim]\n")

    print_summary(len(violations))

    return len(violations) > 0

@app.command()
def check(
    pr: int = typer.Option(None, help="Validate a specific PR"),
    explain: bool = typer.Option(False, "--explain", help="Explain violations using AI")
):
    """Validate current codebase against schema."""
    if pr:
        console.print(f"[yellow]Note: PR fetching for PR #{pr} is mocked for this MVP.[/yellow]")

    has_violations = _run_checks(explain)
    if has_violations:
        raise typer.Exit(1)

@app.command()
def watch():
    """Watch mode — re-validate on file changes."""
    console.print("[cyan]Starting watch mode... (Press Ctrl+C to exit)[/cyan]")
    # MVP simple watch loop
    last_run = 0
    try:
        while True:
            # Check if any .py or .yml files changed
            needs_run = False
            for root, _, files in os.walk("."):
                if ".git" in root:
                    continue
                for f in files:
                    if f.endswith(".py") or f.endswith(".yml"):
                        f_path = os.path.join(root, f)
                        if os.path.getmtime(f_path) > last_run:
                            needs_run = True
                            break
                if needs_run:
                    break

            if needs_run:
                os.system("clear" if os.name == "posix" else "cls")
                _run_checks()
                last_run = time.time()

            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[cyan]Exiting watch mode.[/cyan]")

@app.command()
def graph():
    """Visualize dependency graph."""
    if not Path(SCHEMA_FILE).exists():
        console.print(f"[red]Error: {SCHEMA_FILE} not found.[/red]")
        raise typer.Exit(1)

    schema = ArchSchema.load(SCHEMA_FILE)
    import_graph = scan_imports(".", schema)

    console.print("[bold cyan]Dependency Graph[/bold cyan]")
    for svc, imports in import_graph.imports.items():
        targets = {stmt.service for stmt in imports}
        if targets:
            console.print(f"[green]{svc}[/green] → {', '.join(targets)}")
        else:
            console.print(f"[green]{svc}[/green] (no dependencies)")

@app.command()
def install_hook():
    """Install as pre-commit hook."""
    hook_dir = Path(".git/hooks")
    if not hook_dir.exists():
        console.print("[red]Error: .git/hooks directory not found. Are you in the repo root?[/red]")
        raise typer.Exit(1)

    hook_file = hook_dir / "pre-commit"

    hook_content = """#!/bin/sh
echo "Running ArchGuard checks..."
archguard check
if [ $? -ne 0 ]; then
    echo "ArchGuard validation failed. Commit aborted."
    exit 1
fi
"""
    with open(hook_file, "w") as f:
        f.write(hook_content)

    os.chmod(hook_file, 0o755)
    console.print("[green]Successfully installed ArchGuard pre-commit hook.[/green]")

if __name__ == "__main__":
    app()
