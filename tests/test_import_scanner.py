
from archguard.import_scanner import scan_imports
from archguard.schema import ArchSchema


def test_scan_imports():
    schema = ArchSchema.load("tests/fixtures/.archguard.yml")
    graph = scan_imports("tests/fixtures/sample_arch", schema)

    assert "auth-service" in graph.imports
    assert "user-service" in graph.imports

    # auth-service imports user-service in tests/fixtures/sample_arch/auth_service/clients/user_client.py
    auth_imports = graph.imports["auth-service"]
    assert any(stmt.service == "user-service" for stmt in auth_imports)

    # user-service imports auth-service in tests/fixtures/sample_arch/user_service/auth/verify.py
    user_imports = graph.imports["user-service"]
    assert any(stmt.service == "auth-service" for stmt in user_imports)

    # notification-service imports payment-service in sender.py
    notif_imports = graph.imports["notification-service"]
    assert any(stmt.service == "payment-service" and stmt.module_path == "payment_service.models" for stmt in notif_imports)
