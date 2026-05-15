from typing import Any

from rich.console import Console

console = Console()

def print_header(schema_file: str, num_services: int, num_rules: int, num_files: int = 0):
    console.print()
    console.print("ArchGuard — Architecture Validation", style="bold cyan")
    console.print("──────────────────────────────────────────────────", style="cyan")
    console.print(f"[bold yellow]✦[/bold yellow] Schema loaded       {schema_file} ({num_services} services, {num_rules} rules)")
    if num_files > 0:
        console.print(f"[bold yellow]✦[/bold yellow] Files checked       {num_files} changed files")
    console.print()

def print_violation_header(title: str):
    console.print(f"  [bold red]── VIOLATION: {title} [/bold red]" + "─" * (30 - len(title)))

def print_cycle(cycle: Any):
    print_violation_header("Circular Dependency")
    chain = "  →  ".join(cycle.services)
    console.print(f"  [bold]{chain}[/bold]")
    console.print(f"  Introduced by: {cycle.introduced_by}:{cycle.line}")
    console.print()

def print_contract_breach(breach: Any):
    print_violation_header("Contract Breach")
    console.print(f"  [bold]{breach.service}[/bold] exposes: {breach.endpoint_path}")
    console.print(f"  Changed: {breach.description}")
    consumers_str = ", ".join(breach.consumers) if breach.consumers else "None"
    console.print(f"  Consumers expecting old schema: [bold]{consumers_str}[/bold]")
    console.print()

def print_boundary_violation(violation: Any):
    print_violation_header("Boundary Breach")
    console.print(f"  [bold]{violation.from_service}[/bold] imports from [bold]{violation.to_service}[/bold] internals")
    console.print(f"  {violation.file_path}:{violation.line}")
    console.print(f"    from {violation.imported_module} import ...")
    console.print(f"  Rule: {violation.rule_broken}")
    console.print()

def print_summary(num_violations: int):
    if num_violations == 0:
        console.print("[bold green]✦ 0 violations found — merge permitted[/bold green]")
    else:
        console.print(f"[bold red]✦ {num_violations} violations found — merge blocked[/bold red]")
    console.print("──────────────────────────────────────────────────", style="cyan")
    console.print()
