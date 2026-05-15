from archguard.boundary_checker import check_boundaries
from archguard.import_scanner import scan_imports
from archguard.schema import ArchSchema


def test_check_boundaries():
    schema = ArchSchema.load("tests/fixtures/.archguard.yml")
    graph = scan_imports("tests/fixtures/sample_arch", schema)
    violations = check_boundaries(graph, schema)

    # notification-service imports payment_service.models, which is not public.
    assert len(violations) >= 1

    notification_violations = [v for v in violations if v.from_service == "notification-service"]
    assert len(notification_violations) > 0
    violation = notification_violations[0]

    assert violation.to_service == "payment-service"
    assert violation.imported_module == "payment_service.models"
    assert "not in the public API" in violation.rule_broken
