from dataclasses import dataclass
from typing import Dict, List

import networkx as nx

from .import_scanner import ImportData


@dataclass
class Cycle:
    services: List[str]
    introduced_by: str
    line: int

def detect_cycles(import_graph: Dict[str, Dict[str, List[ImportData]]]) -> List[Cycle]:
    G = nx.DiGraph()

    for service, imports in import_graph.items():
        G.add_node(service)
        for target in imports.keys():
            G.add_node(target)
            G.add_edge(service, target)

    try:
        cycles = list(nx.simple_cycles(G))
    except nx.NetworkXNoCycle:
        return []

    result = []
    seen = set()
    for cycle in cycles:
        cycle_key = tuple(sorted(cycle))
        if cycle_key in seen:
            continue
        seen.add(cycle_key)

        # Find exactly where the cycle was introduced
        # We look at the last edge in the cycle to blame it
        source = cycle[-1]
        target = cycle[0]

        import_data_list = import_graph.get(source, {}).get(target, [])
        if import_data_list:
            import_data = import_data_list[0]
            result.append(Cycle(
                services=cycle,
                introduced_by=import_data.file_path,
                line=import_data.line
            ))

    return result
