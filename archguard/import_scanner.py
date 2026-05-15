import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from .schema import ArchSchema, ServiceSchema


@dataclass
class ImportStatement:
    service: str            # The service that is being imported FROM
    module_path: str        # The raw module path e.g. "payment_service.models"
    file_path: str          # The file doing the importing
    line_number: int        # The line number of the import


class ImportGraph:
    def __init__(self):
        # Maps service name -> list of specific import statements
        self.imports: Dict[str, List[ImportStatement]] = {}

    def add_import(self, from_service: str, statement: ImportStatement):
        if from_service not in self.imports:
            self.imports[from_service] = []
        self.imports[from_service].append(statement)

    def get_imported_services(self, from_service: str) -> Set[str]:
        return {stmt.service for stmt in self.imports.get(from_service, [])}


def find_service_by_module(module_name: str, services: List[ServiceSchema]) -> str | None:
    # First, treat module dots as path separators to match service.path
    module_path = module_name.replace(".", "/")

    # Sort services by path length descending to match deepest first
    sorted_services = sorted(services, key=lambda s: len(s.path), reverse=True)

    for s in sorted_services:
        service_path = s.path.rstrip("/")
        if module_path.startswith(service_path):
            return s.name

    # Try just by top-level package matching service path's top level folder
    top_level = module_name.split(".")[0]
    for s in sorted_services:
        if s.path.startswith(f"{top_level}/") or s.path == top_level or s.path == f"{top_level}/":
            return s.name

    return None

class ImportVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, current_service: str, services: List[ServiceSchema], graph: ImportGraph):
        self.file_path = file_path
        self.current_service = current_service
        self.services = services
        self.graph = graph

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name
            self._handle_import(module_name, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            module_name = node.module
            # Handle relative imports (this is simplified)
            if node.level > 0:
                pass # Skipping relative imports for now, assume they don't cross service boundaries directly easily
            else:
                self._handle_import(module_name, node.lineno)
        self.generic_visit(node)

    def _handle_import(self, module_name: str, lineno: int):
        target_service = find_service_by_module(module_name, self.services)
        if target_service and target_service != self.current_service:
            stmt = ImportStatement(
                service=target_service,
                module_path=module_name,
                file_path=self.file_path,
                line_number=lineno
            )
            self.graph.add_import(self.current_service, stmt)

def scan_imports(base_dir: str, schema: ArchSchema) -> ImportGraph:
    graph = ImportGraph()
    base_path = Path(base_dir)

    # Initialize all services in the graph
    for service in schema.services:
        if service.name not in graph.imports:
            graph.imports[service.name] = []

    for service in schema.services:
        service_path = base_path / service.path
        if not service_path.exists() or not service_path.is_dir():
            continue

        for py_file in service_path.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                tree = ast.parse(content, filename=str(py_file))

                # Make paths relative to base_dir for cleaner reporting
                rel_path = str(py_file.relative_to(base_path))

                visitor = ImportVisitor(rel_path, service.name, schema.services, graph)
                visitor.visit(tree)
            except SyntaxError:
                pass # Ignore syntax errors in unparseable files

    return graph
