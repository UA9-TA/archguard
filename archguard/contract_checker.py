import json
import os
import subprocess
from dataclasses import dataclass
from typing import List

import yaml
from deepdiff import DeepDiff

from .schema import ArchSchema


@dataclass
class ContractViolation:
    service: str
    endpoint: str
    consumers: List[str]
    diff: str

def load_schema_file(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        if filepath.endswith('.yml') or filepath.endswith('.yaml'):
            return yaml.safe_load(f) or {}
        return json.load(f)

def load_schema_file_from_git(filepath: str) -> dict:
    try:
        content = subprocess.check_output(
            ["git", "show", f"HEAD:{filepath}"],
            stderr=subprocess.DEVNULL
        ).decode('utf-8')
        if filepath.endswith('.yml') or filepath.endswith('.yaml'):
            return yaml.safe_load(content) or {}
        return json.loads(content)
    except Exception:
        return {}

def check_contracts(schema: ArchSchema) -> List[ContractViolation]:
    violations = []

    if not schema.rules.enforce_public_api_contracts:
        return violations

    for service in schema.services:
        for public_api in service.public_api:
            if not public_api.schema:
                continue

            old_schema = load_schema_file_from_git(public_api.schema)
            new_schema = load_schema_file(public_api.schema)

            if old_schema and new_schema:
                diff = DeepDiff(old_schema, new_schema, ignore_order=True)

                # Check for breaking changes (type changes, dictionary item removals)
                is_breaking = False
                if 'dictionary_item_removed' in diff or 'type_changes' in diff or 'values_changed' in diff:
                    is_breaking = True

                if is_breaking:
                    consumers = [s.name for s in schema.services if service.name in s.may_import_from]
                    violations.append(ContractViolation(
                        service=service.name,
                        endpoint=public_api.path,
                        consumers=consumers,
                        diff=str(diff)
                    ))

    return violations
