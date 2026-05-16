import ast
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

from .schema import ArchSchema


@dataclass
class ImportData:
    module: str
    file_path: str
    line: int

def resolve_module_name(node, file_path):
    if isinstance(node, ast.Import):
        return [n.name for n in node.names]
    elif isinstance(node, ast.ImportFrom):
        module = node.module if node.module else ''
        level = node.level if node.level else 0
        if level > 0:
            dir_parts = os.path.dirname(file_path).split(os.sep)
            if level <= len(dir_parts):
                base = '.'.join(dir_parts[:-level + 1])
                module = f"{base}.{module}" if module else base
        return [module]
    return []

def get_service_for_module(module: str, schema: ArchSchema) -> str | None:
    for service in schema.services:
        path = service.path.rstrip('/')
        if module.replace('.', '/').startswith(path):
            return service.name
    return None

def get_service_for_file(file_path: str, schema: ArchSchema) -> str | None:
    for service in schema.services:
        if file_path.startswith(service.path):
            return service.name
    return None

def scan_imports(schema: ArchSchema, base_dir: str = ".") -> Dict[str, Dict[str, List[ImportData]]]:
    graph = defaultdict(lambda: defaultdict(list))

    for service in schema.services:
        service_dir = os.path.join(base_dir, service.path)
        if not os.path.exists(service_dir):
            continue

        for root, _, files in os.walk(service_dir):
            for file in files:
                if not file.endswith('.py'):
                    continue
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir)

                with open(file_path, 'r') as f:
                    try:
                        content = f.read()
                        tree = ast.parse(content, filename=file_path)
                    except SyntaxError:
                        continue

                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        modules = resolve_module_name(node, rel_path)
                        for module in modules:
                            if not module:
                                continue
                            imported_service = get_service_for_module(module, schema)
                            if imported_service and imported_service != service.name:
                                graph[service.name][imported_service].append(
                                    ImportData(module=module, file_path=rel_path, line=node.lineno)
                                )

    return dict(graph)
