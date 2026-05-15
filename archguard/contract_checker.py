import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List

import yaml

from .schema import ArchSchema


@dataclass
class ContractBreach:
    service: str
    endpoint_path: str
    consumers: List[str]
    description: str

def get_git_file_content(filepath: str, ref: str = "HEAD") -> str | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{filepath}"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None

def check_contracts(schema: ArchSchema) -> List[ContractBreach]:
    breaches = []

    # We only care about this rule if enabled
    if not schema.rules.enforce_public_api_contracts:
        return breaches

    for service in schema.services:
        for endpoint in service.public_api:
            if not endpoint.schema:
                continue

            # Read current schema
            try:
                with open(endpoint.schema, "r") as f:
                    current_content = f.read()
                    current_yaml = yaml.safe_load(current_content)
            except FileNotFoundError:
                continue

            # Read previous schema from HEAD
            previous_content = get_git_file_content(endpoint.schema)
            if not previous_content:
                continue

            previous_yaml = yaml.safe_load(previous_content)

            # Simple diff: check if any properties in responses were removed or renamed
            # In a real app this would use a full OpenAPI diff tool.
            # For this MVP, we do a naive check on response schemas.

            breach_found = detect_breaking_changes(previous_yaml, current_yaml)
            if breach_found:
                consumers = []
                for other_service in schema.services:
                    if service.name in other_service.may_import_from:
                        consumers.append(other_service.name)

                breaches.append(ContractBreach(
                    service=service.name,
                    endpoint_path=endpoint.path,
                    consumers=consumers,
                    description=breach_found
                ))

    return breaches

def detect_breaking_changes(old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> str | None:
    """
    Very naive check for breaking changes in OpenAPI paths.
    Checks if properties were removed from a response object.
    """
    if not isinstance(old_schema, dict) or not isinstance(new_schema, dict):
        return None

    old_paths = old_schema.get("paths", {})
    new_paths = new_schema.get("paths", {})

    for path, old_methods in old_paths.items():
        if path not in new_paths:
            return f"Path {path} removed"

        new_methods = new_paths[path]
        for method, old_op in old_methods.items():
            if method not in new_methods:
                return f"Method {method.upper()} on {path} removed"

            old_responses = old_op.get("responses", {})
            new_responses = new_methods[method].get("responses", {})

            for status, old_response in old_responses.items():
                if status not in new_responses:
                    return f"Response {status} removed for {method.upper()} {path}"

                # Dig into content -> application/json -> schema -> properties
                old_props = _get_properties(old_response)
                new_props = _get_properties(new_responses[status])

                for prop_name in old_props:
                    if prop_name not in new_props:
                        return f"Property '{prop_name}' removed from {status} response of {method.upper()} {path}"

    return None

def _get_properties(response_obj: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return response_obj["content"]["application/json"]["schema"]["properties"]
    except KeyError:
        return {}
