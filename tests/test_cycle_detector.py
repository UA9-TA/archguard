from archguard.cycle_detector import detect_cycles
from archguard.import_scanner import ImportData


def test_detect_cycles():
    import_graph = {
        'auth-service': {
            'user-service': [ImportData('user_service', 'auth/clients/user_client.py', 12)]
        },
        'user-service': {
            'auth-service': [ImportData('auth_service', 'user/auth/verify.py', 2)]
        }
    }

    cycles = detect_cycles(import_graph)
    assert len(cycles) == 1
    assert 'auth-service' in cycles[0].services
    assert 'user-service' in cycles[0].services
