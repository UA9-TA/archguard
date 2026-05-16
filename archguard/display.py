
from rich.console import Console

from .boundary_checker import BoundaryViolation
from .contract_checker import ContractViolation
from .cycle_detector import Cycle

console = Console()

def print_header(schema_path: str, num_services: int, num_rules: int):
    console.print()
    console.print("[bold cyan]ArchGuard — Architecture Validation[/bold cyan]")
    console.print("──────────────────────────────────────────────────")
    console.print(f"✦ Schema loaded       [green]{schema_path}[/green] ({num_services} services, {num_rules} rules)")

def print_cycle(cycle: Cycle):
    console.print()
    console.print("  [bold red]── VIOLATION: Circular Dependency ───────────────[/bold red]")

    path = "  →  ".join(cycle.services + [cycle.services[0]])
    console.print(f"  {path}")
    console.print(f"  Introduced by: {cycle.introduced_by}:{cycle.line}")

def print_boundary(violation: BoundaryViolation):
    console.print()
    console.print("  [bold red]── VIOLATION: Boundary Breach ────────────────────[/bold red]")
    console.print(f"  {violation.source_service} imports from {violation.target_service} internals")
    console.print(f"  {violation.file_path}:{violation.line}")
    console.print(f"    from {violation.module} import ...")
    console.print(f"  Rule: {violation.reason}")

def print_contract(violation: ContractViolation):
    console.print()
    console.print("  [bold red]── VIOLATION: Contract Breach ────────────────────[/bold red]")
    console.print(f"  {violation.service} exposes: {violation.endpoint}")
    console.print("  Changed schema detected")
    consumers_str = ", ".join(violation.consumers) if violation.consumers else "none"
    console.print(f"  Consumers: {consumers_str}")

def print_summary(num_violations: int):
    console.print()
    if num_violations > 0:
        console.print(f"✦ [bold red]{num_violations} violations found — merge blocked[/bold red]")
    else:
        console.print("✦ [bold green]No violations found — architecture is clean[/bold green]")
    console.print("──────────────────────────────────────────────────")
