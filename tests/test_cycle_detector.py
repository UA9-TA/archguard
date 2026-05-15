from archguard.cycle_detector import detect_cycles
from archguard.import_scanner import scan_imports
from archguard.schema import ArchSchema


def test_detect_cycles():
    schema = ArchSchema.load("tests/fixtures/.archguard.yml")
    graph = scan_imports("tests/fixtures/sample_arch", schema)
    cycles = detect_cycles(graph)

    assert len(cycles) > 0
    cycle = cycles[0]

    assert set(cycle.services) == {"auth-service", "user-service"}
    assert cycle.introduced_by is not None
    assert cycle.line > 0
