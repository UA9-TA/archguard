from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class PublicApi:
    path: str
    schema: Optional[str] = None

@dataclass
class Service:
    name: str
    path: str
    public_api: List[PublicApi] = field(default_factory=list)
    may_import_from: List[str] = field(default_factory=list)

@dataclass
class Rules:
    no_circular_dependencies: bool = True
    enforce_public_api_contracts: bool = True
    no_internal_imports: bool = True

@dataclass
class ArchSchema:
    version: int
    services: List[Service]
    rules: Rules

def load_schema(filepath: str) -> ArchSchema:
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError(f"Empty schema in {filepath}")

    version = data.get('version', 1)
    services_data = data.get('services', [])
    rules_data = data.get('rules', [])

    rules_dict = {}
    if isinstance(rules_data, list):
        for r in rules_data:
            if isinstance(r, dict):
                rules_dict.update(r)
    elif isinstance(rules_data, dict):
        rules_dict = rules_data

    rules = Rules(**rules_dict)

    services = []
    for s in services_data:
        public_api_data = s.get('public_api', [])
        public_api = [PublicApi(**api) for api in public_api_data]
        service = Service(
            name=s.get('name'),
            path=s.get('path'),
            public_api=public_api,
            may_import_from=s.get('may_import_from', [])
        )
        services.append(service)

    return ArchSchema(version=version, services=services, rules=rules)
