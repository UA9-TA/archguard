from dataclasses import dataclass
from typing import List

from .import_scanner import ImportGraph
from .schema import ArchSchema


@dataclass
class BoundaryViolation:
    from_service: str
    to_service: str
    file_path: str
    line: int
    imported_module: str
    rule_broken: str

def check_boundaries(graph: ImportGraph, schema: ArchSchema) -> List[BoundaryViolation]:
    violations = []

    for from_service, imports in graph.imports.items():
        from_schema = schema.get_service(from_service)
        if not from_schema:
            continue

        allowed_services = set(from_schema.may_import_from)

        for stmt in imports:
            to_service = stmt.service
            to_schema = schema.get_service(to_service)
            if not to_schema:
                continue

            # Check 1: Is from_service allowed to import to_service at all?
            if to_service not in allowed_services:
                violations.append(BoundaryViolation(
                    from_service=from_service,
                    to_service=to_service,
                    file_path=stmt.file_path,
                    line=stmt.line_number,
                    imported_module=stmt.module_path,
                    rule_broken=f"Service '{from_service}' is not allowed to import from '{to_service}'"
                ))
                continue

            # Check 2: Are they importing a public API?
            if schema.rules.no_internal_imports:
                is_public = False

                # Check if the imported module matches any public API path
                # Convert dot path to file path equivalent for checking
                module_path_as_file = stmt.module_path.replace(".", "/")

                for endpoint in to_schema.public_api:
                    # Very simple glob-like matching:
                    # e.g., path: payment/api.py or path: payment/api/*
                    pub_path = endpoint.path.replace(".py", "") # Strip .py for easy module comparison

                    if pub_path.endswith("*"):
                        base_path = pub_path[:-1].rstrip("/")
                        if module_path_as_file.startswith(base_path):
                            is_public = True
                            break
                    else:
                        if module_path_as_file == pub_path or module_path_as_file.startswith(pub_path + "/"):
                            is_public = True
                            break

                if not is_public and to_schema.public_api: # If public_api is empty, we assume nothing is public
                    violations.append(BoundaryViolation(
                        from_service=from_service,
                        to_service=to_service,
                        file_path=stmt.file_path,
                        line=stmt.line_number,
                        imported_module=stmt.module_path,
                        rule_broken=f"Imported module '{stmt.module_path}' is not in the public API of '{to_service}'"
                    ))

    return violations
