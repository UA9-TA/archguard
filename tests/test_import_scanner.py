import os

from archguard.import_scanner import scan_imports
from archguard.schema import load_schema


def test_scan_imports():
    schema_path = os.path.join(os.path.dirname(__file__), 'fixtures', '.archguard.yml')
    base_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    schema = load_schema(schema_path)

    import_graph = scan_imports(schema, base_dir=base_dir)

    assert 'auth-service' in import_graph
    assert 'user-service' in import_graph['auth-service']

    assert 'user-service' in import_graph
    assert 'auth-service' in import_graph['user-service']

    assert 'notification-service' in import_graph
    assert 'payment-service' in import_graph['notification-service']
