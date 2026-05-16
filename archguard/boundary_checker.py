from dataclasses import dataclass
from typing import Dict, List

from .import_scanner import ImportData
from .schema import ArchSchema


@dataclass
class BoundaryViolation:
    source_service: str
    target_service: str
    module: str
    file_path: str
    line: int
    reason: str

def check_boundaries(schema: ArchSchema, import_graph: Dict[str, Dict[str, List[ImportData]]]) -> List[BoundaryViolation]:
    violations = []

    service_map = {s.name: s for s in schema.services}

    for source_name, imports in import_graph.items():
        source_service = service_map.get(source_name)
        if not source_service:
            continue

        for target_name, import_data_list in imports.items():
            target_service = service_map.get(target_name)
            if not target_service:
                continue

            for import_data in import_data_list:
                # Rule 1: check may_import_from
                if target_name not in source_service.may_import_from:
                    violations.append(BoundaryViolation(
                        source_service=source_name,
                        target_service=target_name,
                        module=import_data.module,
                        file_path=import_data.file_path,
                        line=import_data.line,
                        reason=f"{source_name} is not allowed to import from {target_name}"
                    ))
                    continue

                # Rule 2: check public api boundaries
                if schema.rules.no_internal_imports:
                    module_path = import_data.module.replace('.', '/')
                    if not module_path.endswith('.py'):
                        module_path = module_path + '/'

                    is_public = False
                    for public_api in target_service.public_api:
                        api_path = public_api.path.strip('/')
                        if api_path.endswith('/*'):
                            prefix = api_path[:-2]
                            if module_path.startswith(prefix):
                                is_public = True
                                break
                        elif module_path.startswith(api_path):
                            is_public = True
                            break

                    if not is_public:
                        violations.append(BoundaryViolation(
                            source_service=source_name,
                            target_service=target_name,
                            module=import_data.module,
                            file_path=import_data.file_path,
                            line=import_data.line,
                            reason=f"Importing internal module {import_data.module} from {target_name}"
                        ))

    return violations
