"""Pure graph helpers (no DB, no third-party imports) so they are easy to unit-test.

Edges are (prerequisite_id, concept_id) tuples meaning  prerequisite -> concept.
"""
from collections import defaultdict, deque
from collections.abc import Iterable


def build_adjacency(edges: Iterable[tuple[int, int]]):
    prereqs: dict[int, set[int]] = defaultdict(set)    # concept -> its direct prerequisites
    dependents: dict[int, set[int]] = defaultdict(set)  # prerequisite -> concepts that need it
    for pre, con in edges:
        prereqs[con].add(pre)
        dependents[pre].add(con)
    return prereqs, dependents


def _reach(start: int, adjacency: dict[int, set[int]]) -> set[int]:
    seen: set[int] = set()
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nxt in adjacency.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    seen.discard(start)
    return seen


def descendants(node: int, dependents: dict[int, set[int]]) -> set[int]:
    """Every concept that (directly or indirectly) depends on `node`."""
    return _reach(node, dependents)


def ancestors(node: int, prereqs: dict[int, set[int]]) -> set[int]:
    """Every concept that `node` (directly or indirectly) requires."""
    return _reach(node, prereqs)


def would_create_cycle(prerequisite_id: int, concept_id: int, edges: Iterable[tuple[int, int]]) -> bool:
    """True if adding  prerequisite_id -> concept_id  would create a cycle.

    A cycle appears when the prerequisite already (indirectly) depends on the concept,
    i.e. the concept can already reach the prerequisite by following dependents.
    """
    if prerequisite_id == concept_id:
        return True
    _, dependents = build_adjacency(edges)
    return prerequisite_id in descendants(concept_id, dependents)


def compute_depths(node_ids: Iterable[int], edges: Iterable[tuple[int, int]]) -> dict[int, int]:
    """Depth = length of the longest prerequisite chain below a concept (roots have depth 0)."""
    node_ids = list(node_ids)
    prereqs, _ = build_adjacency(edges)
    memo: dict[int, int] = {}
    visiting: set[int] = set()

    def depth(n: int) -> int:
        if n in memo:
            return memo[n]
        if n in visiting:  # defensive: a cycle should never exist
            return 0
        visiting.add(n)
        d = 0 if not prereqs.get(n) else 1 + max(depth(p) for p in prereqs[n])
        visiting.discard(n)
        memo[n] = d
        return d

    return {n: depth(n) for n in node_ids}
