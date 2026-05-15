from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class PublicApiEndpoint:
    path: str
    schema: Optional[str] = None


@dataclass
class ServiceSchema:
    name: str
    path: str
    public_api: List[PublicApiEndpoint] = field(default_factory=list)
    may_import_from: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceSchema":
        public_api_data = data.get("public_api", [])
        public_api = []
        for api_item in public_api_data:
            public_api.append(PublicApiEndpoint(
                path=api_item.get("path"),
                schema=api_item.get("schema")
            ))
        return cls(
            name=data["name"],
            path=data["path"],
            public_api=public_api,
            may_import_from=data.get("may_import_from", [])
        )


@dataclass
class RulesSchema:
    no_circular_dependencies: bool = True
    enforce_public_api_contracts: bool = True
    no_internal_imports: bool = True

    @classmethod
    def from_list(cls, rules_data: List[Dict[str, bool]]) -> "RulesSchema":
        rules = cls()
        for rule_dict in rules_data:
            if "no_circular_dependencies" in rule_dict:
                rules.no_circular_dependencies = rule_dict["no_circular_dependencies"]
            if "enforce_public_api_contracts" in rule_dict:
                rules.enforce_public_api_contracts = rule_dict["enforce_public_api_contracts"]
            if "no_internal_imports" in rule_dict:
                rules.no_internal_imports = rule_dict["no_internal_imports"]
        return rules


@dataclass
class ArchSchema:
    version: int
    services: List[ServiceSchema]
    rules: RulesSchema

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "ArchSchema":
        data = yaml.safe_load(yaml_content)
        if not data:
            raise ValueError("Empty or invalid YAML file.")

        version = data.get("version", 1)
        services_data = data.get("services", [])
        services = [ServiceSchema.from_dict(s) for s in services_data]

        rules_data = data.get("rules", [])
        rules = RulesSchema.from_list(rules_data)

        # Validate that all 'may_import_from' reference valid service names
        service_names = {s.name for s in services}
        for s in services:
            for dep in s.may_import_from:
                if dep not in service_names:
                    raise ValueError(f"Service '{s.name}' may_import_from unknown service: '{dep}'")

        return cls(version=version, services=services, rules=rules)

    @classmethod
    def load(cls, file_path: str | Path) -> "ArchSchema":
        with open(file_path, "r", encoding="utf-8") as f:
            return cls.from_yaml(f.read())

    def get_service(self, name: str) -> Optional[ServiceSchema]:
        for service in self.services:
            if service.name == name:
                return service
        return None
