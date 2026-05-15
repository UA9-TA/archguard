from dataclasses import dataclass
from typing import List, Set

import networkx as nx

from .import_scanner import ImportGraph


@dataclass
class Cycle:
    services: List[str]      # e.g., ["auth-service", "user-service", "auth-service"]
    introduced_by: str       # file path
    line: int

def detect_cycles(graph: ImportGraph) -> List[Cycle]:
    G = nx.DiGraph()

    # Track the edges that introduce dependencies, so we can report them
    # Maps (from_svc, to_svc) -> ImportStatement
    edge_reasons = {}

    for from_svc, imports in graph.imports.items():
        if from_svc not in G:
            G.add_node(from_svc)
        for stmt in imports:
            to_svc = stmt.service
            if to_svc not in G:
                G.add_node(to_svc)

            # If there are multiple imports between two services, just keeping the first is enough for the cycle report
            if (from_svc, to_svc) not in edge_reasons:
                edge_reasons[(from_svc, to_svc)] = stmt
            G.add_edge(from_svc, to_svc)

    try:
        cycles_iter = nx.simple_cycles(G)
    except nx.NetworkXNoCycle:
        return []

    detected_cycles = []
    # To avoid reporting the same cycle with different starting points, we canonicalize
    seen_canonical_cycles: Set[tuple] = set()

    for cycle in cycles_iter:
        if len(cycle) < 2:
            continue # Self-loops aren't handled, or maybe they are? (A->A)

        canonical = tuple(sorted(cycle))
        if canonical in seen_canonical_cycles:
            continue
        seen_canonical_cycles.add(canonical)

        # A cycle like ['auth-service', 'user-service'] means auth -> user -> auth
        full_cycle_path = cycle + [cycle[0]]

        # Find which edge "introduced" the cycle. This is usually arbitrary in a static graph,
        # but we can pick one (e.g. the last edge in the path)
        u = full_cycle_path[-2]
        v = full_cycle_path[-1]
        stmt = edge_reasons[(u, v)]

        detected_cycles.append(Cycle(
            services=full_cycle_path,
            introduced_by=stmt.file_path,
            line=stmt.line_number
        ))

    return detected_cycles
