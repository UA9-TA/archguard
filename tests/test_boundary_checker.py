import os

from archguard.boundary_checker import check_boundaries
from archguard.import_scanner import ImportData
from archguard.schema import load_schema


def test_check_boundaries():
    schema_path = os.path.join(os.path.dirname(__file__), 'fixtures', '.archguard.yml')
    schema = load_schema(schema_path)

    import_graph = {
        'notification-service': {
            'payment-service': [
                ImportData('sample_arch.payment_service.models', 'notification/sender.py', 8)
            ]
        }
    }

    violations = check_boundaries(schema, import_graph)
    assert len(violations) == 1
    assert violations[0].source_service == 'notification-service'
    assert violations[0].target_service == 'payment-service'
    assert 'models' in violations[0].module
