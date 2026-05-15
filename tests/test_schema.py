import pytest

from archguard.schema import ArchSchema


def test_load_schema():
    yaml_content = """
    version: 1
    services:
      - name: s1
        path: s1/
        may_import_from: []
    rules:
      - no_circular_dependencies: true
    """
    schema = ArchSchema.from_yaml(yaml_content)
    assert schema.version == 1
    assert len(schema.services) == 1
    assert schema.services[0].name == "s1"
    assert schema.rules.no_circular_dependencies is True

def test_invalid_dependency():
    yaml_content = """
    version: 1
    services:
      - name: s1
        path: s1/
        may_import_from: [s2]
    """
    with pytest.raises(ValueError, match="unknown service: 's2'"):
        ArchSchema.from_yaml(yaml_content)
